import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class VolumeController:
    def __init__(self):
        self.devices = AudioUtilities.GetSpeakers()
        self.volume = self.devices.EndpointVolume
        
        self.volRange = self.volume.GetVolumeRange()
        self.minVol = self.volRange[0]
        self.maxVol = self.volRange[1]
        
    def get_current_volume(self):
        return self.volume.GetMasterVolumeLevel()

    def set_volume(self, length, min_length=50, max_length=250):
        """
        Maps the distance (length) to the system volume range and sets it.
        Returns the new volume and the mapped percentage.
        """
        volBar = np.interp(length, [min_length, max_length], [400, 150])
        volPer = np.interp(length, [min_length, max_length], [0, 100])
        volScalar = np.interp(length, [min_length, max_length], [0.0, 1.0])
        
        # Set the system volume
        try:
            self.volume.SetMasterVolumeLevelScalar(volScalar, None)
        except Exception:
            vol = np.interp(length, [min_length, max_length], [self.minVol, self.maxVol])
            self.volume.SetMasterVolumeLevel(vol, None)
        
        return volScalar, volBar, volPer
