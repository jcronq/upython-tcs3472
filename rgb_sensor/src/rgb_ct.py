
def isSaturated(self, r, g, b, c):
    if (c <= 0):
        return True
    
    if ((256 - self._integration_time) > 63):
        # Track digital saturation
        sat = 65535
    else:
        # Track analog saturation 
        sat = 1024 * (256 - self._integration_time)
    
    if ((256 - self._integration_time) <= 63):
        # Adjust sat to 75% to avoid analog saturation if atime < 153.6ms
        sat -= sat / 4

    # Check for saturation and mark the sample as invalid if true 
    if (c >= sat):
        return True
    
    return False

def cleanColorData(self, red, green, blue, clear):        
    ir = (red + green + blue) - clear
            
    red   -= ir * self.irWeight['r']
    green -= ir * self.irWeight['g']
    blue  -= ir * self.irWeight['b']
    
    r_light = (self.redWeight['r'] * red) + (self.redWeight['g'] * green) + (self.redWeight['b'] * blue) 
    g_light = (self.greenWeight['r'] * red) + (self.greenWeight['g'] * green) + (self.greenWeight['b'] * blue) 
    b_light = (self.blueWeight['r'] * red) + (self.blueWeight['g'] * green) + (self.blueWeight['b'] * blue) 
    
    intensity = (clear / min((256 - self._integration_time)*1024, 65535 )) * 255
    
    total = r_light + g_light + b_light
    r = (r_light/total) * intensity
    g = (g_light/total) * intensity
    b = (b_light/total) * intensity
    
    return r, g, b
    
def getRGB(self):
    [red, green, blue, clear] = self.get_raw_data()
    
    r = (red / clear) * 255
    g = (green / clear) * 255
    b = (blue / clear) * 255
    return [r, g, b]

def get_color_temperature(self, r, g, b):
    X = (-0.14282 * r) + (1.54924 * g) + (-0.95641 * b)
    Y = (-0.32466 * r) + (1.57837 * g) + (-0.73191 * b)
    Z = (-0.68202 * r) + (0.77073 * g) + ( 0.56332 * b)

    xc = (X) / (X + Y + Z)
    yc = (Y) / (X + Y + Z)

    n = (xc - 0.3320) / (0.1858 - yc)
    cct = (449.0 * (n ** 3)) + (3525.0 * (n ** 2)) + (6823.3 * n) + 5520.33

    return cct

def getColorTempJason(self, r, g, b):
    if(r <= 0):
        return 0
            
    return (3810 * b) / r + 1391

def get_color_temp(self, r, g, b, c):
    if (c <= 0):
        return 0
    if ((256 - self._integration_time) > 63):
        # Track digital saturation
        sat = 65535
    else:
        # Track analog saturation 
        sat = 1024 * (256 - self._integration_time)
    
    if ((256 - self._integration_time) <= 63):
        sat -= sat / 4

    if (c >= sat):
        return 0
    
    ir = 0
    if(r + g + b > c):
        ir = (r + g + b - c) / 3

    r2 = r - ir
    b2 = b - ir

    if (r2 <= 0):
        return 0

    cct = (3810 * b2) / r2 + 1391

    return cct