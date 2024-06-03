class PID_Control:
 
    def __init__(self, _dt, _min, _max, _kp, _ki, _kd):
        self.update(_dt, _min, _max, _kp, _ki, _kd)
 
        self.pre_error = 0
        self.integral = 0
        self.area_under_curve = 0  # Inicializamos el área bajo la curva

 
    def update(self, _dt, _min, _max, _kp, _ki, _kd):
        self.dt = _dt
        self.min = _min
        self.max = _max
        self.kp = _kp
        self.ki = _ki
        self.kd = _kd
 
    def calc(self, sv, pv):
        error = sv - pv
        # Proporcional
        kp = self.kp * error
 
        # Integral
        self.integral += error * self.dt
        ki = self.ki * self.integral

        # Calculamos el área bajo la curva del error acumulando el valor absoluto del error en cada paso de tiempo
        # fórmula de la suma de Riemann para integrales definidas.
        self.area_under_curve += abs(error) * self.dt
 
        # Derivativo
        kd = (error - self.pre_error) / self.dt
        kd = self.kd * kd
 
        # Suma
        result = kp + ki + kd
 
        if result > self.max:
            result = self.max
        elif result < self.min:
            result = self.min
 
        self.pre_error = error
 
        # Descripción
        desc = f'Kp :\t{kp:.3f}\nKi :\t{ki:.3f}\nKd :\t{kd:.3f}\nPv :\t{pv:.3f}\nSv :\t{sv:.3f}\nArea bajo la curva de error :\t{self.area_under_curve:.3f}'
 
        return result, desc
