from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import numpy as np

class AudioController:
    def __init__(self):
        self.activated = False
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            self.volume = devices.EndpointVolume
            volRange = self.volume.GetVolumeRange()
            self.minVol = volRange[0]
            self.maxVol = volRange[1]
            self.activated = True
        except Exception as e:
            print(f"Volume interface setup failed: {e}")
            self.minVol, self.maxVol = -65.25, 0.0
            
    def set_volume_by_y(self, y_val, y_min, y_max):
        if not self.activated:
            return 0
            
        vol = np.interp(y_val, [y_min, y_max], [self.maxVol, self.minVol])
        try:
            self.volume.SetMasterVolumeLevel(vol, None)
        except Exception:
            pass
            
        return np.interp(y_val, [y_min, y_max], [400, 150]) # returns bar height for UI
