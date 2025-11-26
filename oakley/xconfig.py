
import json
import os


class XConfig(dict):
    
    # ---------------------- #
    # !-- Initialization --! #
    # ---------------------- #
    
    def __init__(self, filepath:str, default_config:dict = {}):
        """
        Implements a dictionary that automatically saves to a JSON file on every change.
        
        Parameters
        ----------
        filepath : str
            Path to the JSON config file. If a directory is given, saves as 'config.json' inside that directory.
        default_config : dict or list of str, optional
            Default configuration to use if the file does not exist. By default, an empty dictionary is used. This will be
            automatically dumped to the file if it does not exist.
        
        Notes
        -----
        - The directory containing the config file must exist beforehand.
        - Every time a value is changed in the dictionary, the JSON file is automatically updated. This behavior can be
          disabled by setting the `autosave` attribute to False.
        
        Example
        -------
        >>> config = XConfig('path/to/config.json', default_config={'setting1': True, 'setting2': 42})
        >>> config['setting1'] = False  # This will automatically update the JSON file.
        
        Or inside a python file:
        ```python
        from oakley import XConfig
        import os
        config = XConfig(os.path.join(os.path.dirname(__file__), 'data')) # saves in 'data/config.json', automatically loaded next time!
        """
        assert isinstance(filepath, str), "filepath must be a string"
        assert isinstance(default_config, dict), "default_config must be a dictionnary"
        
        assert filepath.endswith('.json') or os.path.isdir(filepath), "filepath must be a .json file or a directory"
        
        # 1. Parse arguments
        if filepath.endswith('.json'):
            # it's a file
            self._filepath = filepath
        else:
            # it's a directory
            self._filepath = os.path.join(filepath, 'config.json')

        # check that the directory exists
        assert os.path.exists(os.path.dirname(self._filepath)), f"Directory does not exist: {os.path.dirname(self._filepath)}"
        self.autosave = True
        self._default_config = default_config
        
        # 3. Load the config file
        self._load() # calls super().__init__() on the loaded file
        self._dump()
        
        
    # ---------- #
    # !-- IO --! #
    # ---------- #
    
    def _dump(self):
        with open(self._filepath, 'w') as f:
            json.dump(self, f, indent=4)
            
    def _load(self):
        if not os.path.exists(self._filepath):
            # create the file with default config
            with open(self._filepath, 'w') as f:
                json.dump(self._default_config, f, indent=4)
        
        with open(self._filepath, 'r') as f:
            file_config = json.load(f)
        super().__init__(file_config)
        
    def reset(self):
        """
        Resets the config to the (hard coded) default values.
        """
        json.dump(self._default_config, open(self._filepath, 'w'), indent=4)
        self._load()
        
    def delete(self):
        """
        Deletes the config file.
        """
        os.remove(self._filepath)
    
    
    
    
    # ------------------------- #
    # !-- Overriden methods --! #
    # ------------------------- #
    
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        # directly update the config file on every change
        if self.autosave:
            self._dump()
        
    

# ------------------------------- #
# !-- Package Config Instance --! #
# ------------------------------- #

_default_config = {
    "terminal_width": -1, # if -1, auto-detect,
    "spinner": [],
    "root_file": "README.md"
}

_config_path = os.path.join(os.path.dirname(__file__), 'config.json')
oakley_config = XConfig(_config_path, default_config=_default_config)





if __name__ == "__main__":
    _test_config_path = oakley_config._filepath.replace('config.json', 'test_config.json')
    test_config = XConfig(_test_config_path, default_config={"a": 1, "b": 2})
    print("Initial config:", test_config)
    test_config['a'] = 42
    print("Updated config:", test_config)
    test_config.reset()
    print("Reset config:", test_config)
    test_config['c'] = 0
    
    import time
    time.sleep(5) # check the json file
    test_config.delete()
    
    