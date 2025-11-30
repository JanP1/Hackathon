class TimeManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TimeManager, cls).__new__(cls)
            cls._instance.time_scale = 1.0
            cls._instance.delta_time = 0.0  # raw dt in seconds
            cls._instance.scaled_delta_time = 0.0  # scaled dt in seconds
            cls._instance.current_time = 0.0  # scaled accumulated time in ms
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls()
        return cls._instance

    def update(self, dt: float):
        """
        dt: raw delta time in seconds
        """
        if dt < 0:
            dt = 0
        self.delta_time = dt
        self.scaled_delta_time = dt * self.time_scale
        self.current_time += self.scaled_delta_time * 1000.0

    def set_time_scale(self, scale: float):
        self.time_scale = scale

    @property
    def dt(self):
        """Scaled delta time in seconds"""
        return self.scaled_delta_time

    @property
    def dt_ms(self):
        """Scaled delta time in milliseconds"""
        return self.scaled_delta_time * 1000.0
    
    @property
    def time(self):
        """Scaled accumulated time in milliseconds"""
        return self.current_time
