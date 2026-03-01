import fastf1
import pandas as pd
import numpy as np
import os

class F1DataQuery:
    def __init__(self, cache_dir='f1_cache'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        fastf1.Cache.enable_cache(self.cache_dir)
        self.session = None

    def load_session(self, year, event, session_name='R'):
        """
        Load an F1 session dynamically.
        session_name can be 'R' (Race), 'Q' (Qualifying), etc.
        """
        self.session = fastf1.get_session(year, event, session_name)
        self.session.load()
        return self.session

    def get_track_layout(self):
        """
        Returns X, Y coordinates of the track.
        """
        if not self.session:
            return None, None
            
        # We can extract the track shape from the fastest lap telemetry,
        # or lap telemetry of the winner.
        fastest_lap = self.session.laps.pick_fastest()
        telemetry = fastest_lap.get_telemetry()
        
        # return X and Y coordinates
        x = telemetry['X'].values
        y = telemetry['Y'].values
        return x, y
        
    def get_drivers(self):
        if not self.session:
            return []
        
        drivers = []
        for driver_number in self.session.drivers:
            driver_info = self.session.get_driver(driver_number)
            drivers.append({
                'number': driver_number,
                'abb': driver_info['Abbreviation'],
                'color': driver_info['TeamColor'],
                'name': f"{driver_info['FirstName']} {driver_info['LastName']}"
            })
        return drivers

    def get_all_laps(self):
        """
        Get laps with telemetry for all drivers.
        Returns a dictionary mapping driver abbreviation to a dataframe of their full race telemetry.
        """
        if not self.session:
            return {}

        driver_telemetry = {}
        for drv in self.session.drivers:
            driver_info = self.session.get_driver(drv)
            abb = driver_info['Abbreviation']
            
            drv_laps = self.session.laps.pick_driver(drv)
            # Only laps that have telemetry
            # We can use `get_telemetry()` on the whole collection of laps for a driver
            try:
                # get_telemetry returns telemetry for all laps in the DataFrame
                telemetry = drv_laps.get_telemetry()
                driver_telemetry[abb] = telemetry
            except Exception as e:
                print(f"Could not load telemetry for {abb}: {e}")
        
        return driver_telemetry
        
    def get_laps_data(self):
        """
        Returns lap-by-lap data for leaderboard.
        """
        return self.session.laps
