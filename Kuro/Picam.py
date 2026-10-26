"""
Picam Python Wrapper - Teledyne Princeton Instruments Camera Control API
Based on picam.h header file

This module provides a comprehensive Python interface to the Picam DLL,
supporting all camera models including the Kuro series.
"""

import ctypes
from ctypes import Structure, c_int, c_double, c_char, c_void_p, POINTER, c_bool
from enum import IntEnum, IntFlag
from typing import List, Tuple
import os
import sys

PICAM_DLL_PATH = r"C:\Program Files\Princeton Instruments\PICam\Runtime\Picam.dll"
# Platform-specific DLL loading
if sys.platform == "win32":
    try:
        # Try to load the DLL from the current directory
        _picam_dll = ctypes.WinDLL(PICAM_DLL_PATH)
    except OSError:
        # If not found, try common installation paths
        possible_paths = [
            r"C:\Program Files\Princeton Instruments\Picam\Picam.dll",
            r"C:\Program Files (x86)\Princeton Instruments\Picam\Picam.dll",
            os.path.join(os.path.dirname(__file__), "Picam.dll")
        ]
        for path in possible_paths:
            if os.path.exists(path):
                _picam_dll = ctypes.WinDLL(path)
                break
        else:
            raise ImportError("Picam.dll not found. Please ensure it's in the PATH or current directory.")
else:
    raise ImportError("This wrapper is designed for Windows platforms with Picam.dll")

# Type definitions matching pil_platform.h
piint = c_int
piflt = c_double
pibln = c_bool
pi64s = ctypes.c_int64
pichar = c_char

# Function calling convention
PIL_CALL = ctypes.WINFUNCTYPE

# Export/Import definitions
PIL_EXPORT_DEF = ctypes.WINFUNCTYPE
PIL_IMPORT = ctypes.WINFUNCTYPE

# Function pointer type
PICAM_FUNCTION = PIL_IMPORT
PICAM_API = PICAM_FUNCTION

# Error Codes
class PicamError(IntEnum):
    """Function return error codes"""
    # Success
    None_ = 0
    
    # General Errors
    UnexpectedError = 4
    UnexpectedNullPointer = 3
    InvalidPointer = 35
    InvalidCount = 39
    EnumerationValueNotDefined = 17
    InvalidOperation = 42
    OperationCanceled = 43
    
    # Library Initialization Errors
    LibraryNotInitialized = 1
    LibraryAlreadyInitialized = 5
    
    # General String Handling Errors
    InvalidEnumeratedType = 16
    
    # Camera/Accessory Plug 'n Play Discovery Errors
    NotDiscoveringCameras = 18
    AlreadyDiscoveringCameras = 19
    NotDiscoveringAccessories = 48
    AlreadyDiscoveringAccessories = 49
    
    # Camera/Accessory Access Errors
    NoCamerasAvailable = 34
    CameraAlreadyOpened = 7
    InvalidCameraID = 8
    NoAccessoriesAvailable = 45
    AccessoryAlreadyOpened = 46
    InvalidAccessoryID = 47
    InvalidHandle = 9
    DeviceCommunicationFailed = 15
    DeviceDisconnected = 23
    DeviceOpenElsewhere = 24
    
    # Demo Camera Errors
    InvalidDemoModel = 6
    InvalidDemoSerialNumber = 21
    DemoAlreadyConnected = 22
    DemoNotSupported = 40
    OnlyDemoSupported = 55
    
    # Camera/Accessory Parameter Access Errors
    ParameterHasInvalidValueType = 11
    ParameterHasInvalidConstraintType = 13
    ParameterDoesNotExist = 12
    ParameterValueIsReadOnly = 10
    InvalidParameterValue = 2
    InvalidConstraintCategory = 38
    ParameterValueIsIrrelevant = 14
    ParameterIsNotOnlineable = 25
    ParameterIsNotReadable = 26
    ParameterIsNotWaitableStatus = 50
    InvalidWaitableStatusParameterTimeOut = 51
    
    # Camera Data Acquisition Errors
    InvalidParameterValues = 28
    ParametersNotCommitted = 29
    InvalidAcquisitionBuffer = 30
    InvalidReadoutCount = 36
    InvalidReadoutTimeOut = 37
    InsufficientMemory = 31
    AcquisitionInProgress = 20
    AcquisitionNotInProgress = 27
    TimeOutOccurred = 32
    AcquisitionUpdatedHandlerRegistered = 33
    InvalidAcquisitionState = 44
    NondestructiveReadoutEnabled = 41
    ShutterOverheated = 52
    CenterWavelengthFaulted = 54
    CameraFaulted = 53

# Enumerated Types
class PicamEnumeratedType(IntEnum):
    """Enumerated type definitions"""
    # Function Return Error Codes
    Error = 1
    
    # General String Handling
    EnumeratedType = 29
    
    # Camera/Accessory Identification
    Model = 2
    ComputerInterface = 3
    
    # Camera/Accessory Plug 'n Play Discovery
    DiscoveryAction = 26
    
    # Camera/Accessory Access
    HandleType = 27
    
    # Camera/Accessory Parameters
    ValueType = 4
    ConstraintType = 5
    Parameter = 6
    
    # Camera/Accessory Parameter Values - Enumerated Types
    ActiveShutter = 53
    AdcAnalogGain = 7
    AdcQuality = 8
    CcdCharacteristicsMask = 9
    CenterWavelengthStatus = 51
    CoolingFanStatus = 56
    EMIccdGainControlMode = 42
    GateTrackingMask = 36
    GatingMode = 34
    GatingSpeed = 38
    GratingCoating = 48
    GratingType = 49
    IntensifierOptionsMask = 35
    IntensifierStatus = 33
    LaserOutputMode = 45
    LaserStatus = 54
    LightSource = 46
    LightSourceStatus = 47
    ModulationTrackingMask = 41
    OrientationMask = 10
    OutputSignal = 11
    PhosphorType = 39
    PhotocathodeSensitivity = 40
    PhotonDetectionMode = 43
    PixelFormat = 12
    ReadoutControlMode = 13
    SensorTemperatureStatus = 14
    SensorType = 15
    ShutterStatus = 52
    ShutterTimingMode = 16
    ShutterType = 50
    TimeStampsMask = 17
    TriggerCoupling = 30
    TriggerDetermination = 18
    TriggerResponse = 19
    TriggerSource = 31
    TriggerStatus = 55
    TriggerTermination = 32
    VacuumStatus = 57
    
    # Camera/Accessory Parameter Information - Value Access
    ValueAccess = 20
    
    # Camera/Accessory Parameter Information - Dynamics
    DynamicsMask = 28
    
    # Camera/Accessory Parameter Constraints - Enumerated Types
    ConstraintScope = 21
    ConstraintSeverity = 22
    ConstraintCategory = 23
    
    # Camera Parameter Constraints - Regions of Interest
    RoisConstraintRulesMask = 24
    
    # Camera Acquisition Control
    AcquisitionErrorsMask = 25
    
    # Camera Acquisition Notification
    AcquisitionState = 37
    AcquisitionStateErrorsMask = 44

# Camera Models
class PicamModel(IntEnum):
    """Camera model definitions including Kuro series"""
    # PI-MTE Series (1419)
    PIMteSeries = 1400
    PIMte1024Series = 1401
    PIMte1024F = 1402
    PIMte1024B = 1403
    PIMte1024BR = 1405
    PIMte1024BUV = 1404
    PIMte1024FTSeries = 1406
    PIMte1024FT = 1407
    PIMte1024BFT = 1408
    PIMte1300Series = 1412
    PIMte1300B = 1413
    PIMte1300R = 1414
    PIMte1300BR = 1415
    PIMte2048Series = 1416
    PIMte2048B = 1417
    PIMte2048BR = 1418
    PIMte2KSeries = 1409
    PIMte2KB = 1410
    PIMte2KBUV = 1411
    
    # PI-MTE3 Series (2006)
    PIMte3Series = 2000
    PIMte32048Series = 2001
    PIMte32048B = 2002
    PIMte34096Series = 2003
    PIMte34096B = 2004
    PIMte34096B_2 = 2005
    
    # PIXIS Series (76)
    PixisSeries = 0
    Pixis100Series = 1
    Pixis100F = 2
    Pixis100B = 6
    Pixis100R = 3
    Pixis100C = 4
    Pixis100BR = 5
    Pixis100BExcelon = 54
    Pixis100BRExcelon = 55
    PixisXO100B = 7
    PixisXO100BR = 8
    PixisXB100B = 68
    PixisXB100BR = 69
    Pixis256Series = 26
    Pixis256F = 27
    Pixis256B = 29
    Pixis256E = 28
    Pixis256BR = 30
    PixisXB256BR = 31
    Pixis400Series = 37
    Pixis400F = 38
    Pixis400B = 40
    Pixis400R = 39
    Pixis400BR = 41
    Pixis400BExcelon = 56
    Pixis400BRExcelon = 57
    PixisXO400B = 42
    PixisXB400BR = 70
    Pixis512Series = 43
    Pixis512F = 44
    Pixis512B = 45
    Pixis512BUV = 46
    Pixis512BExcelon = 58
    PixisXO512F = 49
    PixisXO512B = 50
    PixisXF512F = 48
    PixisXF512B = 47
    Pixis1024Series = 9
    Pixis1024F = 10
    Pixis1024B = 11
    Pixis1024BR = 13
    Pixis1024BUV = 12
    Pixis1024BExcelon = 59
    Pixis1024BRExcelon = 60
    PixisXO1024F = 16
    PixisXO1024B = 14
    PixisXO1024BR = 15
    PixisXF1024F = 17
    PixisXF1024B = 18
    PixisXB1024BR = 71
    Pixis1300Series = 51
    Pixis1300F = 52
    Pixis1300F_2 = 75
    Pixis1300B = 53
    Pixis1300BR = 73
    Pixis1300BExcelon = 61
    Pixis1300BRExcelon = 62
    PixisXO1300B = 65
    PixisXF1300B = 66
    PixisXB1300R = 72
    Pixis2048Series = 20
    Pixis2048F = 21
    Pixis2048B = 22
    Pixis2048BR = 67
    Pixis2048BExcelon = 63
    Pixis2048BRExcelon = 74
    PixisXO2048B = 23
    PixisXF2048F = 25
    PixisXF2048B = 24
    Pixis2KSeries = 32
    Pixis2KF = 33
    Pixis2KB = 34
    Pixis2KBUV = 36
    Pixis2KBExcelon = 64
    PixisXO2KB = 35
    
    # Quad-RO Series (104)
    QuadroSeries = 100
    Quadro4096 = 101
    Quadro4096_2 = 103
    Quadro4320 = 102
    
    # ProEM Series (214)
    ProEMSeries = 200
    ProEM512Series = 203
    ProEM512B = 201
    ProEM512BK = 205
    ProEM512BExcelon = 204
    ProEM512BKExcelon = 206
    ProEM1024Series = 207
    ProEM1024B = 202
    ProEM1024BExcelon = 208
    ProEM1600Series = 209
    ProEM1600xx2B = 212
    ProEM1600xx2BExcelon = 210
    ProEM1600xx4B = 213
    ProEM1600xx4BExcelon = 211
    
    # ProEM+ Series (614)
    ProEMPlusSeries = 600
    ProEMPlus512Series = 603
    ProEMPlus512B = 601
    ProEMPlus512BK = 605
    ProEMPlus512BExcelon = 604
    ProEMPlus512BKExcelon = 606
    ProEMPlus1024Series = 607
    ProEMPlus1024B = 602
    ProEMPlus1024BExcelon = 608
    ProEMPlus1600Series = 609
    ProEMPlus1600xx2B = 612
    ProEMPlus1600xx2BExcelon = 610
    ProEMPlus1600xx4B = 613
    ProEMPlus1600xx4BExcelon = 611
    
    # ProEM-HS Series (1218)
    ProEMHSSeries = 1200
    ProEMHS512Series = 1201
    ProEMHS512B = 1202
    ProEMHS512BK = 1207
    ProEMHS512BExcelon = 1203
    ProEMHS512BKExcelon = 1208
    ProEMHS512B_2 = 1216
    ProEMHS512BExcelon_2 = 1217
    ProEMHS1024Series = 1204
    ProEMHS1024B = 1205
    ProEMHS1024BExcelon = 1206
    ProEMHS1024B_2 = 1212
    ProEMHS1024BExcelon_2 = 1213
    ProEMHS1024B_3 = 1214
    ProEMHS1024BExcelon_3 = 1215
    ProEMHS1K10Series = 1209
    ProEMHS1KB10 = 1210
    ProEMHS1KB10Excelon = 1211
    
    # PI-MAX3 Series (303)
    PIMax3Series = 300
    PIMax31024I = 301
    PIMax31024x256 = 302
    
    # PI-MAX4 Series (721)
    PIMax4Series = 700
    PIMax41024ISeries = 703
    PIMax41024I = 701
    PIMax41024IRF = 704
    PIMax41024FSeries = 710
    PIMax41024F = 711
    PIMax41024FRF = 712
    PIMax41024x256Series = 705
    PIMax41024x256 = 702
    PIMax41024x256RF = 706
    PIMax42048Series = 716
    PIMax42048F = 717
    PIMax42048B = 718
    PIMax42048FRF = 719
    PIMax42048BRF = 720
    PIMax4512EMSeries = 708
    PIMax4512EM = 707
    PIMax4512BEM = 709
    PIMax41024EMSeries = 713
    PIMax41024EM = 715
    PIMax41024BEM = 714
    
    # PyLoN Series (439)
    PylonSeries = 400
    Pylon100Series = 418
    Pylon100F = 404
    Pylon100B = 401
    Pylon100BR = 407
    Pylon100BExcelon = 425
    Pylon100BRExcelon = 426
    Pylon256Series = 419
    Pylon256F = 409
    Pylon256B = 410
    Pylon256E = 411
    Pylon256BR = 412
    Pylon400Series = 420
    Pylon400F = 405
    Pylon400B = 402
    Pylon400BR = 408
    Pylon400BExcelon = 427
    Pylon400BRExcelon = 428
    Pylon1024Series = 421
    Pylon1024B = 417
    Pylon1024BExcelon = 429
    Pylon1300Series = 422
    Pylon1300F = 406
    Pylon1300B = 403
    Pylon1300R = 438
    Pylon1300BR = 432
    Pylon1300BExcelon = 430
    Pylon1300BRExcelon = 433
    Pylon2048Series = 423
    Pylon2048F = 415
    Pylon2048B = 434
    Pylon2048BR = 416
    Pylon2048BExcelon = 435
    Pylon2048BRExcelon = 436
    Pylon2KSeries = 424
    Pylon2KF = 413
    Pylon2KB = 414
    Pylon2KBUV = 437
    Pylon2KBExcelon = 431
    
    # PyLoN-IR Series (904)
    PylonirSeries = 900
    Pylonir1024Series = 901
    Pylonir102422 = 902
    Pylonir102417 = 903
    
    # PIoNIR Series (502)
    PionirSeries = 500
    Pionir640 = 501
    
    # NIRvana Series (802)
    NirvanaSeries = 800
    Nirvana640 = 801
    
    # NIRvana ST Series (1302)
    NirvanaSTSeries = 1300
    NirvanaST640 = 1301
    
    # NIRvana-LN Series (1102)
    NirvanaLNSeries = 1100
    NirvanaLN640 = 1101
    
    # NIRvana HS Series (2202)
    NirvanaHSSeries = 2200
    NirvanaHS = 2201
    
    # SOPHIA Series (1847)
    SophiaSeries = 1800
    Sophia2048Series = 1801
    Sophia2048B = 1802
    Sophia2048BExcelon = 1803
    SophiaXO2048B = 1804
    SophiaXF2048B = 1805
    SophiaXB2048B = 1806
    Sophia2048135Series = 1807
    Sophia2048135 = 1808
    Sophia2048B135 = 1809
    Sophia2048BR135 = 1810
    Sophia2048BUV135 = 1844
    Sophia2048B135Excelon = 1811
    Sophia2048BR135Excelon = 1812
    SophiaXO2048B135 = 1813
    SophiaXO2048BR135 = 1814
    Sophia2048B135Excelon_2 = 1840
    Sophia4096Series = 1826
    Sophia4096B = 1827
    SophiaXO4096B = 1829
    SophiaXF4096B = 1830
    SophiaXB4096B = 1831
    Sophia4096B_2 = 1841
    Sophia4096HdrSeries = 1832
    Sophia4096BHdr = 1833
    Sophia4096BRHdr = 1834
    SophiaXO4096BHdr = 1837
    SophiaXO4096BRHdr = 1838
    SophiaXF4096BHdr = 1839
    SophiaXF4096BRHdr = 1828
    SophiaXB4096BHdr = 1835
    SophiaXB4096BRHdr = 1836
    Sophia4096BHdr_2 = 1842
    Sophia4096BRHdr_2 = 1843
    
    # BLAZE Series (1519)
    BlazeSeries = 1500
    Blaze100Series = 1507
    Blaze100B = 1501
    Blaze100BR = 1505
    Blaze100HR = 1503
    Blaze100BRLD = 1509
    Blaze100BExcelon = 1511
    Blaze100BRExcelon = 1513
    Blaze100HRExcelon = 1515
    Blaze100BRLDExcelon = 1517
    Blaze400Series = 1508
    Blaze400B = 1502
    Blaze400BR = 1506
    Blaze400HR = 1504
    Blaze400BRLD = 1510
    Blaze400BExcelon = 1512
    Blaze400BRExcelon = 1514
    Blaze400HRExcelon = 1516
    Blaze400BRLDExcelon = 1518
    
    # FERGIE Series (1612)
    FergieSeries = 1600
    Fergie256Series = 1601
    Fergie256B = 1602
    Fergie256BR = 1607
    Fergie256BExcelon = 1603
    Fergie256BRExcelon = 1608
    Fergie256FTSeries = 1604
    Fergie256FFT = 1609
    Fergie256BFT = 1605
    Fergie256BRFT = 1610
    Fergie256BFTExcelon = 1606
    Fergie256BRFTExcelon = 1611
    
    # FERGIE-ISO-81 Series (2104)
    FergieIso81Series = 2100
    FergieIso81256FTSeries = 2101
    FergieIso81256BFTExcelon = 2102
    FergieIso81256BRFTExcelon = 2103
    
    # FERGIE Accessory Series (1707)
    FergieAccessorySeries = 1700
    FergieLampSeries = 1701
    FergieAEL = 1702
    FergieQTH = 1703
    FergieLaserSeries = 1704
    FergieLaser785 = 1705
    FergieLaser532 = 1706
    
    # KURO Series (1904) - Main focus for this implementation
    KuroSeries = 1900
    Kuro1200B = 1901
    Kuro1608B = 1902
    Kuro2048B = 1903
    
    # IntelliCal Accessory Series (2603)
    IntellicalAccessorySeries = 2600
    IntellicalLampSeries = 2601
    IntellicalSwirQTH = 2602
    
    # TPIR Series (2304)
    TpirSeries = 2300
    Tpir785Series = 2301
    Tpir785100 = 2302
    Tpir785400 = 2303
    
    # TPIR HR Series (2404)
    TpirHRSeries = 2400
    Tpir785HRSeries = 2401
    Tpir785HR100 = 2402
    Tpir785HR400 = 2403
    
    # Evolve Series (2904)
    EvolveSeries = 2900
    Evolve10 = 2901
    Evolve13 = 2902
    Evolve16 = 2903
    
    # LANSIS Series (2720)
    LansisSeries = 2700
    Lansis261Series = 2701
    LansisA261BR = 2702
    LansisA261BRX = 2704
    Lansis424Series = 2711
    LansisD424B = 2712
    LansisD424BX = 2713
    LansisD424BX_2 = 2714
    
    # Retiga Series (3202)
    RetigaSeries = 3200
    RetigaE7 = 3201

# Computer Interface Types
class PicamComputerInterface(IntEnum):
    """Computer interface types"""
    Usb2 = 1
    Usb3 = 4
    Usb31 = 6
    Ieee1394A = 2
    GigabitEthernet = 3

# String Size Constants
class PicamStringSize(IntEnum):
    """String size constants"""
    SensorName = 64
    SerialNumber = 64
    FirmwareName = 64
    FirmwareDetail = 256

# Camera ID Structure
class PicamCameraID(Structure):
    """Camera identification structure"""
    _fields_ = [
        ("model", piint),
        ("computer_interface", piint),
        ("sensor_name", c_char * PicamStringSize.SensorName),
        ("serial_number", c_char * PicamStringSize.SerialNumber)
    ]

# Handle Type
PicamHandle = c_void_p

# Firmware Detail Structure
class PicamFirmwareDetail(Structure):
    """Firmware detail structure"""
    _fields_ = [
        ("name", c_char * PicamStringSize.FirmwareName),
        ("detail", c_char * PicamStringSize.FirmwareDetail)
    ]

# Calibration Structures
class PicamCalibrationPoint(Structure):
    """Calibration point structure"""
    _fields_ = [
        ("x", piflt),
        ("y", piflt)
    ]

class PicamCalibration(Structure):
    """Calibration structure"""
    _fields_ = [
        ("point_array", POINTER(PicamCalibrationPoint)),
        ("point_count", piint)
    ]

# Value Types
class PicamValueType(IntEnum):
    """Parameter value types"""
    Integer = 1
    Boolean = 3
    Enumeration = 4
    LargeInteger = 6
    FloatingPoint = 2
    Rois = 5
    Pulse = 7
    Modulations = 8

# Constraint Types
class PicamConstraintType(IntEnum):
    """Parameter constraint types"""
    None_ = 1
    Range = 2
    Collection = 3
    Rois = 4
    Pulse = 5
    Modulations = 6

# Parameter Definitions (using the PI_V macro equivalent)
def PI_V(value_type, constraint_type, parameter_number):
    """Helper function to create parameter values like the PI_V macro"""
    return ((constraint_type << 24) + (value_type << 16) + parameter_number)

class PicamParameter(IntEnum):
    """Camera/Accessory parameters"""
    # Shutter Timing
    ExposureTime = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 23)
    ExposureTimeResult = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 172)
    ShutterTimingMode = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 24)
    ShutterOpeningDelay = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 46)
    ShutterClosingDelay = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 25)
    ShutterDelayResolution = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Collection, 47)
    InternalShutterType = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 139)
    InternalShutterStatus = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 153)
    ExternalShutterType = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 152)
    ExternalShutterStatus = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 154)
    ActiveShutter = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 155)
    InactiveShutterTimingModeResult = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 156)
    
    # Gating
    GatingMode = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 93)
    RepetitiveGate = PI_V(PicamValueType.Pulse, PicamConstraintType.Pulse, 94)
    SequentialStartingGate = PI_V(PicamValueType.Pulse, PicamConstraintType.Pulse, 95)
    SequentialEndingGate = PI_V(PicamValueType.Pulse, PicamConstraintType.Pulse, 96)
    SequentialGateStepCount = PI_V(PicamValueType.LargeInteger, PicamConstraintType.Range, 97)
    SequentialGateStepIterations = PI_V(PicamValueType.LargeInteger, PicamConstraintType.Range, 98)
    DifStartingGate = PI_V(PicamValueType.Pulse, PicamConstraintType.Pulse, 102)
    DifEndingGate = PI_V(PicamValueType.Pulse, PicamConstraintType.Pulse, 103)
    
    # Intensifier
    EnableIntensifier = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 86)
    IntensifierStatus = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 87)
    IntensifierGain = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 88)
    EMIccdGainControlMode = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 123)
    EMIccdGain = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 124)
    PhosphorDecayDelay = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 89)
    PhosphorDecayDelayResolution = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Collection, 90)
    BracketGating = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 100)
    IntensifierOptions = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 101)
    EnableModulation = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 111)
    ModulationDuration = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 118)
    ModulationFrequency = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 112)
    RepetitiveModulationPhase = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 113)
    SequentialStartingModulationPhase = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 114)
    SequentialEndingModulationPhase = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 115)
    CustomModulationSequence = PI_V(PicamValueType.Modulations, PicamConstraintType.Modulations, 119)
    PhotocathodeSensitivity = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 107)
    GatingSpeed = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 108)
    PhosphorType = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 109)
    IntensifierDiameter = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 110)
    
    # Analog to Digital Conversion
    AdcSpeed = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Collection, 33)
    AdcBitDepth = PI_V(PicamValueType.Integer, PicamConstraintType.Collection, 34)
    AdcAnalogGain = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 35)
    AdcQuality = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 36)
    AdcEMGain = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 53)
    CorrectPixelBias = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 106)
    
    # Hardware I/O
    TriggerSource = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 79)
    TriggerResponse = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 30)
    TriggerDetermination = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 31)
    TriggerFrequency = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 80)
    TriggerTermination = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 81)
    TriggerCoupling = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 82)
    TriggerThreshold = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 83)
    TriggerDelay = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 164)
    OutputSignal = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 32)
    InvertOutputSignal = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 52)
    OutputSignal2 = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 150)
    InvertOutputSignal2 = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 151)
    EnableAuxOutput = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 161)
    AuxOutput = PI_V(PicamValueType.Pulse, PicamConstraintType.Pulse, 91)
    EnableSyncMaster = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 84)
    SyncMaster2Delay = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 85)
    EnableModulationOutputSignal = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 116)
    ModulationOutputSignalFrequency = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 117)
    ModulationOutputSignalAmplitude = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 120)
    AnticipateTrigger = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 131)
    DelayFromPreTrigger = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 132)
    
    # Readout Control
    ReadoutControlMode = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 26)
    ReadoutTimeCalculation = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 27)
    ReadoutPortCount = PI_V(PicamValueType.Integer, PicamConstraintType.Collection, 28)
    ReadoutOrientation = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 54)
    KineticsWindowHeight = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 56)
    SeNsRWindowHeight = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 163)
    VerticalShiftRate = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Collection, 13)
    RowTimeResult = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 171)
    Accumulations = PI_V(PicamValueType.LargeInteger, PicamConstraintType.Range, 92)
    EnableNondestructiveReadout = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 128)
    NondestructiveReadoutPeriod = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 129)
    
    # Data Acquisition
    Rois = PI_V(PicamValueType.Rois, PicamConstraintType.Rois, 37)
    NormalizeOrientation = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 39)
    DisableDataFormatting = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 55)
    ReadoutCount = PI_V(PicamValueType.LargeInteger, PicamConstraintType.Range, 40)
    ExactReadoutCountMaximum = PI_V(PicamValueType.LargeInteger, PicamConstraintType.None_, 77)
    PixelFormat = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 41)
    FrameSize = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 42)
    FrameStride = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 43)
    FramesPerReadout = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 44)
    ReadoutStride = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 45)
    PixelBitDepth = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 48)
    ReadoutRateCalculation = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 50)
    OnlineReadoutRateCalculation = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 99)
    FrameRateCalculation = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 51)
    Orientation = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 38)
    TimeStamps = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 68)
    TimeStampResolution = PI_V(PicamValueType.LargeInteger, PicamConstraintType.Collection, 69)
    TimeStampBitDepth = PI_V(PicamValueType.Integer, PicamConstraintType.Collection, 70)
    TrackFrames = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 71)
    FrameTrackingBitDepth = PI_V(PicamValueType.Integer, PicamConstraintType.Collection, 72)
    GateTracking = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 104)
    GateTrackingBitDepth = PI_V(PicamValueType.Integer, PicamConstraintType.Collection, 105)
    ModulationTracking = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 121)
    ModulationTrackingBitDepth = PI_V(PicamValueType.Integer, PicamConstraintType.Collection, 122)
    
    # Data Processing
    PhotonDetectionMode = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 125)
    PhotonDetectionThreshold = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 126)
    CorrectForDarkCurrent = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 169)
    Despeckle = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 170)
    
    # Sensor Information
    SensorType = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 57)
    CcdCharacteristics = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 58)
    SensorActiveWidth = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 59)
    SensorActiveHeight = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 60)
    SensorActiveExtendedHeight = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 159)
    SensorActiveLeftMargin = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 61)
    SensorActiveTopMargin = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 62)
    SensorActiveRightMargin = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 63)
    SensorActiveBottomMargin = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 64)
    SensorMaskedHeight = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 65)
    SensorMaskedTopMargin = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 66)
    SensorMaskedBottomMargin = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 67)
    SensorSecondaryMaskedHeight = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 49)
    SensorSecondaryActiveHeight = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 74)
    PixelWidth = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 9)
    PixelHeight = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 10)
    PixelGapWidth = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 11)
    PixelGapHeight = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 12)
    ApplicableStarDefectMapID = PI_V(PicamValueType.Integer, PicamConstraintType.None_, 166)
    
    # Sensor Layout
    ActiveWidth = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 1)
    ActiveHeight = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 2)
    ActiveExtendedHeight = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 160)
    ActiveLeftMargin = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 3)
    ActiveTopMargin = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 4)
    ActiveRightMargin = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 5)
    ActiveBottomMargin = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 6)
    MaskedHeight = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 7)
    MaskedTopMargin = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 8)
    MaskedBottomMargin = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 73)
    SecondaryMaskedHeight = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 75)
    SecondaryActiveHeight = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 76)
    
    # Sensor Cleaning
    CleanSectionFinalHeight = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 17)
    CleanSectionFinalHeightCount = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 18)
    CleanSerialRegister = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 19)
    CleanCycleCount = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 20)
    CleanCycleHeight = PI_V(PicamValueType.Integer, PicamConstraintType.Range, 21)
    CleanBeforeExposure = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 78)
    CleanUntilTrigger = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 22)
    StopCleaningOnPreTrigger = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 130)
    
    # Sensor Temperature
    SensorTemperatureSetPoint = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 14)
    SensorTemperatureReading = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 15)
    SensorTemperatureStatus = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 16)
    DisableCoolingFan = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 29)
    CoolingFanStatus = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 162)
    EnableSensorWindowHeater = PI_V(PicamValueType.Boolean, PicamConstraintType.Collection, 127)
    VacuumStatus = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 165)
    
    # Spectrograph
    CenterWavelengthSetPoint = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 140)
    CenterWavelengthReading = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 141)
    CenterWavelengthStatus = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 149)
    GratingType = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 142)
    GratingCoating = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 143)
    GratingGrooveDensity = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 144)
    GratingBlazingWavelength = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 145)
    FocalLength = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 146)
    InclusionAngle = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 147)
    SensorAngle = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 148)
    
    # Laser
    LaserOutputMode = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 137)
    LaserPower = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.Range, 138)
    LaserWavelength = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 167)
    LaserStatus = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 157)
    InputTriggerStatus = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 158)
    
    # Lamp
    LightSource = PI_V(PicamValueType.Enumeration, PicamConstraintType.Collection, 133)
    LightSourceStatus = PI_V(PicamValueType.Enumeration, PicamConstraintType.None_, 134)
    Age = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 135)
    LifeExpectancy = PI_V(PicamValueType.FloatingPoint, PicamConstraintType.None_, 136)

# ROI Structure
class PicamRoi(Structure):
    """Region of Interest structure"""
    _fields_ = [
        ("x", piint),
        ("width", piint),
        ("x_binning", piint),
        ("y", piint),
        ("height", piint),
        ("y_binning", piint)
    ]

class PicamRois(Structure):
    """Regions of Interest structure"""
    _fields_ = [
        ("roi_array", POINTER(PicamRoi)),
        ("roi_count", piint)
    ]

# Pulse Structure
class PicamPulse(Structure):
    """Pulse structure"""
    _fields_ = [
        ("delay", piflt),
        ("width", piflt)
    ]

# Modulation Structure
class PicamModulation(Structure):
    """Modulation structure"""
    _fields_ = [
        ("duration", piflt),
        ("frequency", piflt),
        ("phase", piflt),
        ("output_signal_frequency", piflt)
    ]

class PicamModulations(Structure):
    """Modulations structure"""
    _fields_ = [
        ("modulation_array", POINTER(PicamModulation)),
        ("modulation_count", piint)
    ]

# Enumerated Value Types
class PicamActiveShutter(IntEnum):
    """Active shutter types"""
    None_ = 1
    Internal = 2
    External = 3

class PicamAdcAnalogGain(IntEnum):
    """ADC analog gain types"""
    Low = 1
    Medium = 2
    High = 3

class PicamAdcQuality(IntEnum):
    """ADC quality types"""
    ElectronMultiplied = 3
    LongExposure = 6
    LowNoise = 1
    HighCapacity = 2
    HighDynamicRange = 5
    HighSpeed = 4

class PicamCcdCharacteristicsMask(IntFlag):
    """CCD characteristics mask"""
    None_ = 0x000
    BackIlluminated = 0x001
    DeepDepleted = 0x002
    OpenElectrode = 0x004
    UVEnhanced = 0x008
    ExcelonEnabled = 0x010
    SecondaryMask = 0x020
    Multiport = 0x040
    AdvancedInvertedMode = 0x080
    HighResistivity = 0x100

class PicamCenterWavelengthStatus(IntEnum):
    """Center wavelength status"""
    Moving = 1
    Stationary = 2
    Faulted = 3

class PicamCoolingFanStatus(IntEnum):
    """Cooling fan status"""
    Off = 1
    On = 2
    ForcedOn = 3

class PicamEMIccdGainControlMode(IntEnum):
    """EMI CCD gain control mode"""
    Optimal = 1
    Manual = 2

class PicamGateTrackingMask(IntFlag):
    """Gate tracking mask"""
    None_ = 0x0
    Delay = 0x1
    Width = 0x2

class PicamGatingMode(IntEnum):
    """Gating mode"""
    Disabled = 4
    Repetitive = 1
    Sequential = 2
    Custom = 3

class PicamGatingSpeed(IntEnum):
    """Gating speed"""
    Fast = 1
    Slow = 2

class PicamGratingCoating(IntEnum):
    """Grating coating types"""
    Al = 1
    AlMgF2 = 4
    Ag = 2
    Au = 3

class PicamGratingType(IntEnum):
    """Grating types"""
    Ruled = 1
    HolographicVisible = 2
    HolographicNir = 3
    HolographicUV = 4
    Mirror = 5

class PicamIntensifierOptionsMask(IntFlag):
    """Intensifier options mask"""
    None_ = 0x0
    McpGating = 0x1
    SubNanosecondGating = 0x2
    Modulation = 0x4

class PicamIntensifierStatus(IntEnum):
    """Intensifier status"""
    PoweredOff = 1
    PoweredOn = 2

class PicamLaserOutputMode(IntEnum):
    """Laser output mode"""
    Disabled = 1
    ContinuousWave = 2
    Pulsed = 3

class PicamLaserStatus(IntEnum):
    """Laser status"""
    Disarmed = 1
    Unarmed = 2
    Arming = 3
    Armed = 4

class PicamLightSource(IntEnum):
    """Light source types"""
    Disabled = 1
    Hg = 2
    NeAr = 3
    Qth = 4

class PicamLightSourceStatus(IntEnum):
    """Light source status"""
    Unstable = 1
    Stable = 2

class PicamModulationTrackingMask(IntFlag):
    """Modulation tracking mask"""
    None_ = 0x0
    Duration = 0x1
    Frequency = 0x2
    Phase = 0x4
    OutputSignalFrequency = 0x8

class PicamOrientationMask(IntFlag):
    """Orientation mask"""
    Normal = 0x0
    FlippedHorizontally = 0x1
    FlippedVertically = 0x2

class PicamOutputSignal(IntEnum):
    """Output signal types"""
    Acquiring = 6
    AlwaysHigh = 5
    AlwaysLow = 4
    AuxOutput = 14
    Busy = 3
    EffectivelyExposing = 9
    EffectivelyExposingAlternation = 15
    Exposing = 8
    Gate = 13
    InternalTriggerT0 = 12
    NotReadingOut = 1
    ReadingOut = 10
    ShiftingUnderMask = 7
    ShutterOpen = 2
    WaitingForTrigger = 11

class PicamPhosphorType(IntEnum):
    """Phosphor types"""
    P43 = 1
    P46 = 2

class PicamPhotocathodeSensitivity(IntEnum):
    """Photocathode sensitivity types"""
    RedBlue = 1
    SuperRed = 7
    SuperBlue = 2
    UV = 3
    SolarBlind = 10
    Unigen2Filmless = 4
    InGaAsFilmless = 9
    HighQEFilmless = 5
    HighRedFilmless = 8
    HighBlueFilmless = 6

class PicamPhotonDetectionMode(IntEnum):
    """Photon detection mode"""
    Disabled = 1
    Thresholding = 2
    Clipping = 3

class PicamPixelFormat(IntEnum):
    """Pixel format types"""
    Monochrome16Bit = 1
    Monochrome32Bit = 2

class PicamReadoutControlMode(IntEnum):
    """Readout control mode"""
    FullFrame = 1
    FrameTransfer = 2
    Interline = 5
    GlobalShutter = 10
    RollingShutter = 8
    ExposeDuringReadout = 9
    Kinetics = 3
    SpectraKinetics = 4
    Dif = 6
    SeNsR = 7

class PicamSensorTemperatureStatus(IntEnum):
    """Sensor temperature status"""
    Unlocked = 1
    Locked = 2
    Faulted = 3

class PicamSensorType(IntEnum):
    """Sensor types"""
    Ccd = 1
    InGaAs = 2
    Cmos = 3

class PicamShutterStatus(IntEnum):
    """Shutter status"""
    NotConnected = 1
    Connected = 2
    Overheated = 3

class PicamShutterTimingMode(IntEnum):
    """Shutter timing mode"""
    Normal = 1
    AlwaysClosed = 2
    AlwaysOpen = 3
    OpenBeforeTrigger = 4

class PicamShutterType(IntEnum):
    """Shutter types"""
    None_ = 1
    VincentCS25 = 2
    VincentCS45 = 3
    VincentCS90 = 9
    VincentDSS10 = 8
    VincentVS25 = 4
    VincentVS35 = 5
    ProntorMagnetic0 = 6
    ProntorMagneticE40 = 7

class PicamTimeStampsMask(IntFlag):
    """Time stamps mask"""
    None_ = 0x0
    ExposureStarted = 0x1
    ExposureEnded = 0x2

class PicamTriggerCoupling(IntEnum):
    """Trigger coupling types"""
    AC = 1
    DC = 2

class PicamTriggerDetermination(IntEnum):
    """Trigger determination types"""
    PositivePolarity = 1
    NegativePolarity = 2
    RisingEdge = 3
    FallingEdge = 4
    AlternatingEdgeRising = 5
    AlternatingEdgeFalling = 6

class PicamTriggerResponse(IntEnum):
    """Trigger response types"""
    NoResponse = 1
    StartOnSingleTrigger = 5
    ReadoutPerTrigger = 2
    ShiftPerTrigger = 3
    GatePerTrigger = 6
    ExposeDuringTriggerPulse = 4

class PicamTriggerSource(IntEnum):
    """Trigger source types"""
    None_ = 3
    Internal = 2
    External = 1

class PicamTriggerStatus(IntEnum):
    """Trigger status"""
    NotConnected = 1
    Connected = 2

class PicamTriggerTermination(IntEnum):
    """Trigger termination types"""
    FiftyOhms = 1
    HighImpedance = 2

class PicamVacuumStatus(IntEnum):
    """Vacuum status"""
    Sufficient = 1
    Low = 2

# Value Access Types
class PicamValueAccess(IntEnum):
    """Value access types"""
    ReadOnly = 1
    ReadWriteTrivial = 3
    ReadWrite = 2

# Constraint Types
class PicamConstraintScope(IntEnum):
    """Constraint scope types"""
    Independent = 1
    Dependent = 2

class PicamConstraintSeverity(IntEnum):
    """Constraint severity types"""
    Error = 1
    Warning = 2

class PicamConstraintCategory(IntEnum):
    """Constraint category types"""
    Capable = 1
    Required = 2
    Recommended = 3

# Constraint Structures
class PicamCollectionConstraint(Structure):
    """Collection constraint structure"""
    _fields_ = [
        ("scope", piint),
        ("severity", piint),
        ("values_array", POINTER(piflt)),
        ("values_count", piint)
    ]

class PicamRangeConstraint(Structure):
    """Range constraint structure"""
    _fields_ = [
        ("scope", piint),
        ("severity", piint),
        ("empty_set", pibln),
        ("minimum", piflt),
        ("maximum", piflt),
        ("increment", piflt),
        ("excluded_values_array", POINTER(piflt)),
        ("excluded_values_count", piint),
        ("outlying_values_array", POINTER(piflt)),
        ("outlying_values_count", piint)
    ]

class PicamRoisConstraintRulesMask(IntFlag):
    """ROIs constraint rules mask"""
    None_ = 0x00
    UniformBinning = 0x20
    XBinningAlignment = 0x01
    YBinningAlignment = 0x02
    HorizontalSymmetry = 0x04
    VerticalSymmetry = 0x08
    SymmetryBoundsBinning = 0x10

class PicamRoisConstraint(Structure):
    """ROIs constraint structure"""
    _fields_ = [
        ("scope", piint),
        ("severity", piint),
        ("empty_set", pibln),
        ("rules", piint),
        ("maximum_roi_count", piint),
        ("x_constraint", PicamRangeConstraint),
        ("width_constraint", PicamRangeConstraint),
        ("x_binning_limits_array", POINTER(piint)),
        ("x_binning_limits_count", piint),
        ("y_constraint", PicamRangeConstraint),
        ("height_constraint", PicamRangeConstraint),
        ("y_binning_limits_array", POINTER(piint)),
        ("y_binning_limits_count", piint)
    ]

class PicamPulseConstraint(Structure):
    """Pulse constraint structure"""
    _fields_ = [
        ("scope", piint),
        ("severity", piint),
        ("empty_set", pibln),
        ("delay_constraint", PicamRangeConstraint),
        ("width_constraint", PicamRangeConstraint),
        ("minimum_duration", piflt),
        ("maximum_duration", piflt)
    ]

class PicamModulationsConstraint(Structure):
    """Modulations constraint structure"""
    _fields_ = [
        ("scope", piint),
        ("severity", piint),
        ("empty_set", pibln),
        ("maximum_modulation_count", piint),
        ("duration_constraint", PicamRangeConstraint),
        ("frequency_constraint", PicamRangeConstraint),
        ("phase_constraint", PicamRangeConstraint),
        ("output_signal_frequency_constraint", PicamRangeConstraint)
    ]

# Acquisition Structures
class PicamAvailableData(Structure):
    """Available data structure"""
    _fields_ = [
        ("initial_readout", c_void_p),
        ("readout_count", pi64s)
    ]

class PicamAcquisitionErrorsMask(IntFlag):
    """Acquisition errors mask"""
    None_ = 0x00
    CameraFaulted = 0x10
    ConnectionLost = 0x02
    ShutterOverheated = 0x08
    DataLost = 0x01
    DataNotArriving = 0x04

class PicamAcquisitionStatus(Structure):
    """Acquisition status structure"""
    _fields_ = [
        ("running", pibln),
        ("errors", piint),
        ("readout_rate", piflt)
    ]

class PicamStatusPurview(Structure):
    """Status purview structure"""
    _fields_ = [
        ("values_array", POINTER(piint)),
        ("values_count", piint)
    ]

# Main Picam Class
class Picam:
    """Main Picam class providing Python interface to Picam DLL"""
    
    def __init__(self):
        """Initialize the Picam class"""
        self._dll = _picam_dll
        self._setup_function_signatures()
    
    def _setup_function_signatures(self):
        """Setup function signatures for the DLL functions"""
        # Library Version
        self._dll.Picam_GetVersion.argtypes = [POINTER(piint), POINTER(piint), POINTER(piint), POINTER(piint)]
        self._dll.Picam_GetVersion.restype = piint
        
        # Library Initialization
        self._dll.Picam_IsLibraryInitialized.argtypes = [POINTER(pibln)]
        self._dll.Picam_IsLibraryInitialized.restype = piint
        
        self._dll.Picam_InitializeLibrary.argtypes = []
        self._dll.Picam_InitializeLibrary.restype = piint
        
        self._dll.Picam_UninitializeLibrary.argtypes = []
        self._dll.Picam_UninitializeLibrary.restype = piint
        
        # String Handling
        self._dll.Picam_DestroyString.argtypes = [ctypes.c_char_p]
        self._dll.Picam_DestroyString.restype = piint
        
        # Enumeration String
        self._dll.Picam_GetEnumerationString.argtypes = [piint, piint, POINTER(ctypes.c_char_p)]
        self._dll.Picam_GetEnumerationString.restype = piint
        
        # Camera ID Management
        self._dll.Picam_DestroyCameraIDs.argtypes = [POINTER(PicamCameraID)]
        self._dll.Picam_DestroyCameraIDs.restype = piint
        
        self._dll.Picam_GetAvailableCameraIDs.argtypes = [POINTER(POINTER(PicamCameraID)), POINTER(piint)]
        self._dll.Picam_GetAvailableCameraIDs.restype = piint
        
        self._dll.Picam_GetUnavailableCameraIDs.argtypes = [POINTER(POINTER(PicamCameraID)), POINTER(piint)]
        self._dll.Picam_GetUnavailableCameraIDs.restype = piint
        
        self._dll.Picam_IsCameraIDConnected.argtypes = [POINTER(PicamCameraID), POINTER(pibln)]
        self._dll.Picam_IsCameraIDConnected.restype = piint
        
        self._dll.Picam_IsCameraIDOpenElsewhere.argtypes = [POINTER(PicamCameraID), POINTER(pibln)]
        self._dll.Picam_IsCameraIDOpenElsewhere.restype = piint
        
        # Camera Access
        self._dll.Picam_DestroyHandles.argtypes = [POINTER(PicamHandle)]
        self._dll.Picam_DestroyHandles.restype = piint
        
        self._dll.Picam_OpenFirstCamera.argtypes = [POINTER(PicamHandle)]
        self._dll.Picam_OpenFirstCamera.restype = piint
        
        self._dll.Picam_OpenCamera.argtypes = [POINTER(PicamCameraID), POINTER(PicamHandle)]
        self._dll.Picam_OpenCamera.restype = piint
        
        self._dll.Picam_CloseCamera.argtypes = [PicamHandle]
        self._dll.Picam_CloseCamera.restype = piint
        
        self._dll.Picam_GetOpenCameras.argtypes = [POINTER(POINTER(PicamHandle)), POINTER(piint)]
        self._dll.Picam_GetOpenCameras.restype = piint
        
        self._dll.Picam_IsCameraConnected.argtypes = [PicamHandle, POINTER(pibln)]
        self._dll.Picam_IsCameraConnected.restype = piint
        
        self._dll.Picam_IsCameraFaulted.argtypes = [PicamHandle, POINTER(pibln)]
        self._dll.Picam_IsCameraFaulted.restype = piint
        
        self._dll.Picam_GetCameraID.argtypes = [PicamHandle, POINTER(PicamCameraID)]
        self._dll.Picam_GetCameraID.restype = piint
        
        # Firmware Details
        self._dll.Picam_DestroyFirmwareDetails.argtypes = [POINTER(PicamFirmwareDetail)]
        self._dll.Picam_DestroyFirmwareDetails.restype = piint
        
        self._dll.Picam_GetFirmwareDetails.argtypes = [POINTER(PicamCameraID), POINTER(POINTER(PicamFirmwareDetail)), POINTER(piint)]
        self._dll.Picam_GetFirmwareDetails.restype = piint
        
        # Calibration
        self._dll.Picam_DestroyCalibrations.argtypes = [POINTER(PicamCalibration)]
        self._dll.Picam_DestroyCalibrations.restype = piint
        
        # Demo Camera
        self._dll.Picam_DestroyModels.argtypes = [POINTER(piint)]
        self._dll.Picam_DestroyModels.restype = piint
        
        self._dll.Picam_GetAvailableDemoCameraModels.argtypes = [POINTER(POINTER(piint)), POINTER(piint)]
        self._dll.Picam_GetAvailableDemoCameraModels.restype = piint
        
        self._dll.Picam_ConnectDemoCamera.argtypes = [piint, ctypes.c_char_p, POINTER(PicamCameraID)]
        self._dll.Picam_ConnectDemoCamera.restype = piint
        
        self._dll.Picam_DisconnectDemoCamera.argtypes = [POINTER(PicamCameraID)]
        self._dll.Picam_DisconnectDemoCamera.restype = piint
        
        self._dll.Picam_IsDemoCamera.argtypes = [POINTER(PicamCameraID), POINTER(pibln)]
        self._dll.Picam_IsDemoCamera.restype = piint
        
        # Parameter Value Functions
        self._dll.Picam_GetParameterIntegerValue.argtypes = [PicamHandle, piint, POINTER(piint)]
        self._dll.Picam_GetParameterIntegerValue.restype = piint
        
        self._dll.Picam_SetParameterIntegerValue.argtypes = [PicamHandle, piint, piint]
        self._dll.Picam_SetParameterIntegerValue.restype = piint
        
        self._dll.Picam_CanSetParameterIntegerValue.argtypes = [PicamHandle, piint, piint, POINTER(pibln)]
        self._dll.Picam_CanSetParameterIntegerValue.restype = piint
        
        self._dll.Picam_GetParameterLargeIntegerValue.argtypes = [PicamHandle, piint, POINTER(pi64s)]
        self._dll.Picam_GetParameterLargeIntegerValue.restype = piint
        
        self._dll.Picam_SetParameterLargeIntegerValue.argtypes = [PicamHandle, piint, pi64s]
        self._dll.Picam_SetParameterLargeIntegerValue.restype = piint
        
        self._dll.Picam_CanSetParameterLargeIntegerValue.argtypes = [PicamHandle, piint, pi64s, POINTER(pibln)]
        self._dll.Picam_CanSetParameterLargeIntegerValue.restype = piint
        
        self._dll.Picam_GetParameterFloatingPointValue.argtypes = [PicamHandle, piint, POINTER(piflt)]
        self._dll.Picam_GetParameterFloatingPointValue.restype = piint
        
        self._dll.Picam_SetParameterFloatingPointValue.argtypes = [PicamHandle, piint, piflt]
        self._dll.Picam_SetParameterFloatingPointValue.restype = piint
        
        self._dll.Picam_CanSetParameterFloatingPointValue.argtypes = [PicamHandle, piint, piflt, POINTER(pibln)]
        self._dll.Picam_CanSetParameterFloatingPointValue.restype = piint
        
        # ROI Functions
        self._dll.Picam_DestroyRois.argtypes = [POINTER(PicamRois)]
        self._dll.Picam_DestroyRois.restype = piint
        
        self._dll.Picam_GetParameterRoisValue.argtypes = [PicamHandle, piint, POINTER(POINTER(PicamRois))]
        self._dll.Picam_GetParameterRoisValue.restype = piint
        
        self._dll.Picam_SetParameterRoisValue.argtypes = [PicamHandle, piint, POINTER(PicamRois)]
        self._dll.Picam_SetParameterRoisValue.restype = piint
        
        self._dll.Picam_CanSetParameterRoisValue.argtypes = [PicamHandle, piint, POINTER(PicamRois), POINTER(pibln)]
        self._dll.Picam_CanSetParameterRoisValue.restype = piint
        
        # Pulse Functions
        self._dll.Picam_DestroyPulses.argtypes = [POINTER(PicamPulse)]
        self._dll.Picam_DestroyPulses.restype = piint
        
        self._dll.Picam_GetParameterPulseValue.argtypes = [PicamHandle, piint, POINTER(POINTER(PicamPulse))]
        self._dll.Picam_GetParameterPulseValue.restype = piint
        
        self._dll.Picam_SetParameterPulseValue.argtypes = [PicamHandle, piint, POINTER(PicamPulse)]
        self._dll.Picam_SetParameterPulseValue.restype = piint
        
        self._dll.Picam_CanSetParameterPulseValue.argtypes = [PicamHandle, piint, POINTER(PicamPulse), POINTER(pibln)]
        self._dll.Picam_CanSetParameterPulseValue.restype = piint
        
        # Modulation Functions
        self._dll.Picam_DestroyModulations.argtypes = [POINTER(PicamModulations)]
        self._dll.Picam_DestroyModulations.restype = piint
        
        self._dll.Picam_GetParameterModulationsValue.argtypes = [PicamHandle, piint, POINTER(POINTER(PicamModulations))]
        self._dll.Picam_GetParameterModulationsValue.restype = piint
        
        self._dll.Picam_SetParameterModulationsValue.argtypes = [PicamHandle, piint, POINTER(PicamModulations)]
        self._dll.Picam_SetParameterModulationsValue.restype = piint
        
        self._dll.Picam_CanSetParameterModulationsValue.argtypes = [PicamHandle, piint, POINTER(PicamModulations), POINTER(pibln)]
        self._dll.Picam_CanSetParameterModulationsValue.restype = piint
        
        # Default Value Functions
        self._dll.Picam_GetParameterIntegerDefaultValue.argtypes = [PicamHandle, piint, POINTER(piint)]
        self._dll.Picam_GetParameterIntegerDefaultValue.restype = piint
        
        self._dll.Picam_GetParameterLargeIntegerDefaultValue.argtypes = [PicamHandle, piint, POINTER(pi64s)]
        self._dll.Picam_GetParameterLargeIntegerDefaultValue.restype = piint
        
        self._dll.Picam_GetParameterFloatingPointDefaultValue.argtypes = [PicamHandle, piint, POINTER(piflt)]
        self._dll.Picam_GetParameterFloatingPointDefaultValue.restype = piint
        
        self._dll.Picam_GetParameterRoisDefaultValue.argtypes = [PicamHandle, piint, POINTER(POINTER(PicamRois))]
        self._dll.Picam_GetParameterRoisDefaultValue.restype = piint
        
        self._dll.Picam_GetParameterPulseDefaultValue.argtypes = [PicamHandle, piint, POINTER(POINTER(PicamPulse))]
        self._dll.Picam_GetParameterPulseDefaultValue.restype = piint
        
        self._dll.Picam_GetParameterModulationsDefaultValue.argtypes = [PicamHandle, piint, POINTER(POINTER(PicamModulations))]
        self._dll.Picam_GetParameterModulationsDefaultValue.restype = piint
        
        self._dll.Picam_RestoreParametersToDefaultValues.argtypes = [PicamHandle]
        self._dll.Picam_RestoreParametersToDefaultValues.restype = piint
        
        # Online Parameter Functions
        self._dll.Picam_CanSetParameterOnline.argtypes = [PicamHandle, piint, POINTER(pibln)]
        self._dll.Picam_CanSetParameterOnline.restype = piint
        
        self._dll.Picam_SetParameterIntegerValueOnline.argtypes = [PicamHandle, piint, piint]
        self._dll.Picam_SetParameterIntegerValueOnline.restype = piint
        
        self._dll.Picam_SetParameterFloatingPointValueOnline.argtypes = [PicamHandle, piint, piflt]
        self._dll.Picam_SetParameterFloatingPointValueOnline.restype = piint
        
        self._dll.Picam_SetParameterPulseValueOnline.argtypes = [PicamHandle, piint, POINTER(PicamPulse)]
        self._dll.Picam_SetParameterPulseValueOnline.restype = piint
        
        # Reading Parameter Functions
        self._dll.Picam_CanReadParameter.argtypes = [PicamHandle, piint, POINTER(pibln)]
        self._dll.Picam_CanReadParameter.restype = piint
        
        self._dll.Picam_ReadParameterIntegerValue.argtypes = [PicamHandle, piint, POINTER(piint)]
        self._dll.Picam_ReadParameterIntegerValue.restype = piint
        
        self._dll.Picam_ReadParameterFloatingPointValue.argtypes = [PicamHandle, piint, POINTER(piflt)]
        self._dll.Picam_ReadParameterFloatingPointValue.restype = piint
        
        # Status Parameter Functions
        self._dll.Picam_CanWaitForStatusParameter.argtypes = [PicamHandle, piint, POINTER(pibln)]
        self._dll.Picam_CanWaitForStatusParameter.restype = piint
        
        self._dll.Picam_DestroyStatusPurviews.argtypes = [POINTER(PicamStatusPurview)]
        self._dll.Picam_DestroyStatusPurviews.restype = piint
        
        self._dll.Picam_GetStatusParameterPurview.argtypes = [PicamHandle, piint, POINTER(POINTER(PicamStatusPurview))]
        self._dll.Picam_GetStatusParameterPurview.restype = piint
        
        self._dll.Picam_EstimateTimeToStatusParameterValue.argtypes = [PicamHandle, piint, piint, POINTER(piint)]
        self._dll.Picam_EstimateTimeToStatusParameterValue.restype = piint
        
        self._dll.Picam_WaitForStatusParameterValue.argtypes = [PicamHandle, piint, piint, piint]
        self._dll.Picam_WaitForStatusParameterValue.restype = piint
        
        # Parameter Information Functions
        self._dll.Picam_DestroyParameters.argtypes = [POINTER(piint)]
        self._dll.Picam_DestroyParameters.restype = piint
        
        self._dll.Picam_GetParameters.argtypes = [PicamHandle, POINTER(POINTER(piint)), POINTER(piint)]
        self._dll.Picam_GetParameters.restype = piint
        
        self._dll.Picam_DoesParameterExist.argtypes = [PicamHandle, piint, POINTER(pibln)]
        self._dll.Picam_DoesParameterExist.restype = piint
        
        self._dll.Picam_IsParameterRelevant.argtypes = [PicamHandle, piint, POINTER(pibln)]
        self._dll.Picam_IsParameterRelevant.restype = piint
        
        self._dll.Picam_GetParameterValueType.argtypes = [PicamHandle, piint, POINTER(piint)]
        self._dll.Picam_GetParameterValueType.restype = piint
        
        self._dll.Picam_GetParameterEnumeratedType.argtypes = [PicamHandle, piint, POINTER(piint)]
        self._dll.Picam_GetParameterEnumeratedType.restype = piint
        
        self._dll.Picam_GetParameterValueAccess.argtypes = [PicamHandle, piint, POINTER(piint)]
        self._dll.Picam_GetParameterValueAccess.restype = piint
        
        self._dll.Picam_GetParameterConstraintType.argtypes = [PicamHandle, piint, POINTER(piint)]
        self._dll.Picam_GetParameterConstraintType.restype = piint
        
        # Constraint Functions
        self._dll.Picam_DestroyCollectionConstraints.argtypes = [POINTER(PicamCollectionConstraint)]
        self._dll.Picam_DestroyCollectionConstraints.restype = piint
        
        self._dll.Picam_GetParameterCollectionConstraint.argtypes = [PicamHandle, piint, piint, POINTER(POINTER(PicamCollectionConstraint))]
        self._dll.Picam_GetParameterCollectionConstraint.restype = piint
        
        self._dll.Picam_DestroyRangeConstraints.argtypes = [POINTER(PicamRangeConstraint)]
        self._dll.Picam_DestroyRangeConstraints.restype = piint
        
        self._dll.Picam_GetParameterRangeConstraint.argtypes = [PicamHandle, piint, piint, POINTER(POINTER(PicamRangeConstraint))]
        self._dll.Picam_GetParameterRangeConstraint.restype = piint
        
        self._dll.Picam_DestroyRoisConstraints.argtypes = [POINTER(PicamRoisConstraint)]
        self._dll.Picam_DestroyRoisConstraints.restype = piint
        
        self._dll.Picam_GetParameterRoisConstraint.argtypes = [PicamHandle, piint, piint, POINTER(POINTER(PicamRoisConstraint))]
        self._dll.Picam_GetParameterRoisConstraint.restype = piint
        
        self._dll.Picam_DestroyPulseConstraints.argtypes = [POINTER(PicamPulseConstraint)]
        self._dll.Picam_DestroyPulseConstraints.restype = piint
        
        self._dll.Picam_GetParameterPulseConstraint.argtypes = [PicamHandle, piint, piint, POINTER(POINTER(PicamPulseConstraint))]
        self._dll.Picam_GetParameterPulseConstraint.restype = piint
        
        self._dll.Picam_DestroyModulationsConstraints.argtypes = [POINTER(PicamModulationsConstraint)]
        self._dll.Picam_DestroyModulationsConstraints.restype = piint
        
        self._dll.Picam_GetParameterModulationsConstraint.argtypes = [PicamHandle, piint, piint, POINTER(POINTER(PicamModulationsConstraint))]
        self._dll.Picam_GetParameterModulationsConstraint.restype = piint
        
        # Parameter Commitment
        self._dll.Picam_AreParametersCommitted.argtypes = [PicamHandle, POINTER(pibln)]
        self._dll.Picam_AreParametersCommitted.restype = piint
        
        self._dll.Picam_CommitParameters.argtypes = [PicamHandle, POINTER(POINTER(piint)), POINTER(piint)]
        self._dll.Picam_CommitParameters.restype = piint
        
        # Acquisition Functions
        self._dll.Picam_Acquire.argtypes = [PicamHandle, pi64s, piint, POINTER(PicamAvailableData), POINTER(piint)]
        self._dll.Picam_Acquire.restype = piint
        
        self._dll.Picam_StartAcquisition.argtypes = [PicamHandle]
        self._dll.Picam_StartAcquisition.restype = piint
        
        self._dll.Picam_StopAcquisition.argtypes = [PicamHandle]
        self._dll.Picam_StopAcquisition.restype = piint
        
        self._dll.Picam_IsAcquisitionRunning.argtypes = [PicamHandle, POINTER(pibln)]
        self._dll.Picam_IsAcquisitionRunning.restype = piint
        
        self._dll.Picam_WaitForAcquisitionUpdate.argtypes = [PicamHandle, piint, POINTER(PicamAvailableData), POINTER(PicamAcquisitionStatus)]
        self._dll.Picam_WaitForAcquisitionUpdate.restype = piint
    
    # Library Management Methods
    def GetVersion(self) -> Tuple[int, int, int, int]:
        """Get library version information"""
        major = piint()
        minor = piint()
        distribution = piint()
        released = piint()
        
        error = self._dll.Picam_GetVersion(
            ctypes.byref(major),
            ctypes.byref(minor),
            ctypes.byref(distribution),
            ctypes.byref(released)
        )
        
        if error != PicamError.None_:
            print(PicamException(error))
        
        return major.value, minor.value, distribution.value, released.value
    
    def IsLibraryInitialized(self) -> bool:
        """Check if library is initialized"""
        initialized = pibln()
        error = self._dll.Picam_IsLibraryInitialized(ctypes.byref(initialized))
        if error != PicamError.None_:
            print(PicamException(error))
        return initialized.value
    
    def InitializeLibrary(self):
        """Initialize the library"""
        error = self._dll.Picam_InitializeLibrary()
        if error != PicamError.None_:
            print(PicamException(error))
    
    def UninitializeLibrary(self):
        """Uninitialize the library"""
        error = self._dll.Picam_UninitializeLibrary()
        if error != PicamError.None_:
            print(PicamException(error))
    
    def GetEnumerationString(self, enum_type: PicamEnumeratedType, value: int) -> str:
        """Get enumeration string for a value"""
        string_ptr = ctypes.c_char_p()
        error = self._dll.Picam_GetEnumerationString(enum_type.value, value, ctypes.byref(string_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = string_ptr.value.decode('utf-8')
        self._dll.Picam_DestroyString(string_ptr)
        return result
    
    # Camera Management Methods
    def GetAvailableCameraIDs(self) -> List[PicamCameraID]:
        """Get list of available camera IDs"""
        id_array_ptr = POINTER(PicamCameraID)()
        count = piint()
        
        error = self._dll.Picam_GetAvailableCameraIDs(
            ctypes.byref(id_array_ptr),
            ctypes.byref(count)
        )
        
        if error != PicamError.None_:
            print(PicamException(error))
        
        cameras = []
        for i in range(count.value):
            cameras.append(_copy_struct(id_array_ptr[i]))
        
        self._dll.Picam_DestroyCameraIDs(id_array_ptr)
        return cameras
    
    def GetUnavailableCameraIDs(self) -> List[PicamCameraID]:
        """Get list of unavailable camera IDs"""
        id_array_ptr = POINTER(PicamCameraID)()
        count = piint()
        
        error = self._dll.Picam_GetUnavailableCameraIDs(
            ctypes.byref(id_array_ptr),
            ctypes.byref(count)
        )
        
        if error != PicamError.None_:
            print(PicamException(error))
        
        cameras = []
        for i in range(count.value):
            cameras.append(_copy_struct(id_array_ptr[i]))
        
        self._dll.Picam_DestroyCameraIDs(id_array_ptr)
        return cameras
    
    def IsCameraIDConnected(self, camera_id: PicamCameraID) -> bool:
        """Check if camera ID is connected"""
        connected = pibln()
        error = self._dll.Picam_IsCameraIDConnected(
            ctypes.byref(camera_id),
            ctypes.byref(connected)
        )
        if error != PicamError.None_:
            print(PicamException(error))
        return connected.value
    
    def IsCameraIDOpenElsewhere(self, camera_id: PicamCameraID) -> bool:
        """Check if camera ID is open elsewhere"""
        open_elsewhere = pibln()
        error = self._dll.Picam_IsCameraIDOpenElsewhere(
            ctypes.byref(camera_id),
            ctypes.byref(open_elsewhere)
        )
        if error != PicamError.None_:
            print(PicamException(error))
        return open_elsewhere.value
    
    def OpenFirstCamera(self) -> PicamHandle:
        """Open the first available camera"""
        camera = PicamHandle()
        error = self._dll.Picam_OpenFirstCamera(ctypes.byref(camera))
        if error != PicamError.None_:
            print(PicamException(error))
        return camera
    
    def OpenCamera(self, camera_id: PicamCameraID) -> PicamHandle:
        """Open camera by ID"""
        camera = PicamHandle()
        error = self._dll.Picam_OpenCamera(
            ctypes.byref(camera_id),
            ctypes.byref(camera)
        )
        if error != PicamError.None_:
            print(PicamException(error))
        return camera
    
    def CloseCamera(self, camera: PicamHandle):
        """Close camera"""
        error = self._dll.Picam_CloseCamera(camera)
        if error != PicamError.None_:
            print(PicamException(error))
    
    def GetOpenCameras(self) -> List[PicamHandle]:
        """Get list of open cameras"""
        camera_array_ptr = POINTER(PicamHandle)()
        count = piint()
        
        error = self._dll.Picam_GetOpenCameras(
            ctypes.byref(camera_array_ptr),
            ctypes.byref(count)
        )
        
        if error != PicamError.None_:
            print(PicamException(error))
        
        cameras = []
        for i in range(count.value):
            cameras.append(PicamHandle(camera_array_ptr[i]))
        
        self._dll.Picam_DestroyHandles(camera_array_ptr)
        return cameras
    
    def IsCameraConnected(self, camera: PicamHandle) -> bool:
        """Check if camera is connected"""
        connected = pibln()
        error = self._dll.Picam_IsCameraConnected(camera, ctypes.byref(connected))
        if error != PicamError.None_:
            print(PicamException(error))
        return connected.value
    
    def IsCameraFaulted(self, camera: PicamHandle) -> bool:
        """Check if camera is faulted"""
        faulted = pibln()
        error = self._dll.Picam_IsCameraFaulted(camera, ctypes.byref(faulted))
        if error != PicamError.None_:
            print(PicamException(error))
        return faulted.value
    
    def GetCameraID(self, camera: PicamHandle) -> PicamCameraID:
        """Get camera ID"""
        camera_id = PicamCameraID()
        error = self._dll.Picam_GetCameraID(camera, ctypes.byref(camera_id))
        if error != PicamError.None_:
            print(PicamException(error))
        return camera_id
    
    # Parameter Management Methods
    def GetParameterIntegerValue(self, camera: PicamHandle, parameter: PicamParameter) -> int:
        """Get integer parameter value"""
        value = piint()
        error = self._dll.Picam_GetParameterIntegerValue(camera, parameter.value, ctypes.byref(value))
        if error != PicamError.None_:
            print(PicamException(error))
            return -1
        return value.value
    
    def SetParameterIntegerValue(self, camera: PicamHandle, parameter: PicamParameter, value: int):
        """Set integer parameter value"""
        error = self._dll.Picam_SetParameterIntegerValue(camera, parameter.value, value)
        if error != PicamError.None_:
            print(PicamException(error))
    
    def CanSetParameterIntegerValue(self, camera: PicamHandle, parameter: PicamParameter, value: int) -> bool:
        """Check if integer parameter value can be set"""
        settable = pibln()
        error = self._dll.Picam_CanSetParameterIntegerValue(camera, parameter.value, value, ctypes.byref(settable))
        if error != PicamError.None_:
            print(PicamException(error))
        return settable.value
    
    def GetParameterLargeIntegerValue(self, camera: PicamHandle, parameter: PicamParameter) -> int:
        """Get large integer parameter value"""
        value = pi64s()
        error = self._dll.Picam_GetParameterLargeIntegerValue(camera, parameter.value, ctypes.byref(value))
        if error != PicamError.None_:
            print(PicamException(error))
            return -1
        return value.value
    
    def SetParameterLargeIntegerValue(self, camera: PicamHandle, parameter: PicamParameter, value: int):
        """Set large integer parameter value"""
        error = self._dll.Picam_SetParameterLargeIntegerValue(camera, parameter.value, value)
        if error != PicamError.None_:
            print(PicamException(error))
    
    def CanSetParameterLargeIntegerValue(self, camera: PicamHandle, parameter: PicamParameter, value: int) -> bool:
        """Check if large integer parameter value can be set"""
        settable = pibln()
        error = self._dll.Picam_CanSetParameterLargeIntegerValue(camera, parameter.value, value, ctypes.byref(settable))
        if error != PicamError.None_:
            print(PicamException(error))
        return settable.value
    
    def GetParameterFloatingPointValue(self, camera: PicamHandle, parameter: PicamParameter) -> float:
        """Get floating point parameter value"""
        value = piflt()
        error = self._dll.Picam_GetParameterFloatingPointValue(camera, parameter.value, ctypes.byref(value))
        if error != PicamError.None_:
            print(PicamException(error))
            return -1
        return value.value
    
    def SetParameterFloatingPointValue(self, camera: PicamHandle, parameter: PicamParameter, value: float):
        """Set floating point parameter value"""
        error = self._dll.Picam_SetParameterFloatingPointValue(camera, parameter.value, value)
        if error != PicamError.None_:
            print(PicamException(error))
        return error == PicamError.None_
    
    def CanSetParameterFloatingPointValue(self, camera: PicamHandle, parameter: PicamParameter, value: float) -> bool:
        """Check if floating point parameter value can be set"""
        settable = pibln()
        error = self._dll.Picam_CanSetParameterFloatingPointValue(camera, parameter.value, value, ctypes.byref(settable))
        if error != PicamError.None_:
            print(PicamException(error))
        return settable.value
    
    def GetParameterRoisValue(self, camera: PicamHandle, parameter: PicamParameter) -> PicamRois:
        """Get ROIs parameter value"""
        rois_ptr = POINTER(PicamRois)()
        error = self._dll.Picam_GetParameterRoisValue(camera, parameter.value, ctypes.byref(rois_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(rois_ptr.contents)
        self._dll.Picam_DestroyRois(rois_ptr)
        return result
    
    def SetParameterRoisValue(self, camera: PicamHandle, parameter: PicamParameter, rois: PicamRois):
        """Set ROIs parameter value"""
        error = self._dll.Picam_SetParameterRoisValue(camera, parameter.value, ctypes.byref(rois))
        if error != PicamError.None_:
            print(PicamException(error))
        return error == PicamError.None_
    
    def CanSetParameterRoisValue(self, camera: PicamHandle, parameter: PicamParameter, rois: PicamRois) -> bool:
        """Check if ROIs parameter value can be set"""
        settable = pibln()
        error = self._dll.Picam_CanSetParameterRoisValue(camera, parameter.value, ctypes.byref(rois), ctypes.byref(settable))
        self._dll.Picam_DestroyRois(rois)
        if error != PicamError.None_:
            print(PicamException(error))
        return settable.value
    
    def GetParameterPulseValue(self, camera: PicamHandle, parameter: PicamParameter) -> PicamPulse:
        """Get pulse parameter value"""
        pulse_ptr = POINTER(PicamPulse)()
        error = self._dll.Picam_GetParameterPulseValue(camera, parameter.value, ctypes.byref(pulse_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(pulse_ptr.contents)
        self._dll.Picam_DestroyPulses(pulse_ptr)
        return result
    
    def SetParameterPulseValue(self, camera: PicamHandle, parameter: PicamParameter, pulse: PicamPulse):
        """Set pulse parameter value"""
        error = self._dll.Picam_SetParameterPulseValue(camera, parameter.value, ctypes.byref(pulse))
        if error != PicamError.None_:
            print(PicamException(error))
    
    def CanSetParameterPulseValue(self, camera: PicamHandle, parameter: PicamParameter, pulse: PicamPulse) -> bool:
        """Check if pulse parameter value can be set"""
        settable = pibln()
        error = self._dll.Picam_CanSetParameterPulseValue(camera, parameter.value, ctypes.byref(pulse), ctypes.byref(settable))
        if error != PicamError.None_:
            print(PicamException(error))
        return settable.value
    
    def GetParameterModulationsValue(self, camera: PicamHandle, parameter: PicamParameter) -> PicamModulations:
        """Get modulations parameter value"""
        modulations_ptr = POINTER(PicamModulations)()
        error = self._dll.Picam_GetParameterModulationsValue(camera, parameter.value, ctypes.byref(modulations_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(modulations_ptr.contents)
        self._dll.Picam_DestroyModulations(modulations_ptr)
        return result
    
    def SetParameterModulationsValue(self, camera: PicamHandle, parameter: PicamParameter, modulations: PicamModulations):
        """Set modulations parameter value"""
        error = self._dll.Picam_SetParameterModulationsValue(camera, parameter.value, ctypes.byref(modulations))
        if error != PicamError.None_:
            print(PicamException(error))
    
    def CanSetParameterModulationsValue(self, camera: PicamHandle, parameter: PicamParameter, modulations: PicamModulations) -> bool:
        """Check if modulations parameter value can be set"""
        settable = pibln()
        error = self._dll.Picam_CanSetParameterModulationsValue(camera, parameter.value, ctypes.byref(modulations), ctypes.byref(settable))
        if error != PicamError.None_:
            print(PicamException(error))
        return settable.value
    
    # Default Value Methods
    def GetParameterIntegerDefaultValue(self, camera: PicamHandle, parameter: PicamParameter) -> int:
        """Get integer parameter default value"""
        value = piint()
        error = self._dll.Picam_GetParameterIntegerDefaultValue(camera, parameter.value, ctypes.byref(value))
        if error != PicamError.None_:
            print(PicamException(error))
        return value.value
    
    def GetParameterLargeIntegerDefaultValue(self, camera: PicamHandle, parameter: PicamParameter) -> int:
        """Get large integer parameter default value"""
        value = pi64s()
        error = self._dll.Picam_GetParameterLargeIntegerDefaultValue(camera, parameter.value, ctypes.byref(value))
        if error != PicamError.None_:
            print(PicamException(error))
        return value.value
    
    def GetParameterFloatingPointDefaultValue(self, camera: PicamHandle, parameter: PicamParameter) -> float:
        """Get floating point parameter default value"""
        value = piflt()
        error = self._dll.Picam_GetParameterFloatingPointDefaultValue(camera, parameter.value, ctypes.byref(value))
        if error != PicamError.None_:
            print(PicamException(error))
        return value.value
    
    def GetParameterRoisDefaultValue(self, camera: PicamHandle, parameter: PicamParameter) -> PicamRois:
        """Get ROIs parameter default value"""
        rois_ptr = POINTER(PicamRois)()
        error = self._dll.Picam_GetParameterRoisDefaultValue(camera, parameter.value, ctypes.byref(rois_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(rois_ptr.contents)
        self._dll.Picam_DestroyRois(rois_ptr)
        return result
    
    def GetParameterPulseDefaultValue(self, camera: PicamHandle, parameter: PicamParameter) -> PicamPulse:
        """Get pulse parameter default value"""
        pulse_ptr = POINTER(PicamPulse)()
        error = self._dll.Picam_GetParameterPulseDefaultValue(camera, parameter.value, ctypes.byref(pulse_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(pulse_ptr.contents)
        self._dll.Picam_DestroyPulses(pulse_ptr)
        return result
    
    def GetParameterModulationsDefaultValue(self, camera: PicamHandle, parameter: PicamParameter) -> PicamModulations:
        """Get modulations parameter default value"""
        modulations_ptr = POINTER(PicamModulations)()
        error = self._dll.Picam_GetParameterModulationsDefaultValue(camera, parameter.value, ctypes.byref(modulations_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(modulations_ptr.contents)
        self._dll.Picam_DestroyModulations(modulations_ptr)
        return result
    
    def RestoreParametersToDefaultValues(self, camera: PicamHandle):
        """Restore all parameters to default values"""
        error = self._dll.Picam_RestoreParametersToDefaultValues(camera)
        if error != PicamError.None_:
            print(PicamException(error))
    
    # Online Parameter Methods
    def CanSetParameterOnline(self, camera: PicamHandle, parameter: PicamParameter) -> bool:
        """Check if parameter can be set online"""
        onlineable = pibln()
        error = self._dll.Picam_CanSetParameterOnline(camera, parameter.value, ctypes.byref(onlineable))
        if error != PicamError.None_:
            print(PicamException(error))
        return onlineable.value
    
    def SetParameterIntegerValueOnline(self, camera: PicamHandle, parameter: PicamParameter, value: int):
        """Set integer parameter value online"""
        error = self._dll.Picam_SetParameterIntegerValueOnline(camera, parameter.value, value)
        if error != PicamError.None_:
            print(PicamException(error))
    
    def SetParameterFloatingPointValueOnline(self, camera: PicamHandle, parameter: PicamParameter, value: float):
        """Set floating point parameter value online"""
        error = self._dll.Picam_SetParameterFloatingPointValueOnline(camera, parameter.value, value)
        if error != PicamError.None_:
            print(PicamException(error))
    
    def SetParameterPulseValueOnline(self, camera: PicamHandle, parameter: PicamParameter, pulse: PicamPulse):
        """Set pulse parameter value online"""
        error = self._dll.Picam_SetParameterPulseValueOnline(camera, parameter.value, ctypes.byref(pulse))
        if error != PicamError.None_:
            print(PicamException(error))
    
    # Reading Parameter Methods
    def CanReadParameter(self, camera: PicamHandle, parameter: PicamParameter) -> bool:
        """Check if parameter can be read"""
        readable = pibln()
        error = self._dll.Picam_CanReadParameter(camera, parameter.value, ctypes.byref(readable))
        if error != PicamError.None_:
            print(PicamException(error))
        return readable.value
    
    def ReadParameterIntegerValue(self, camera: PicamHandle, parameter: PicamParameter) -> int:
        """Read integer parameter value"""
        value = piint()
        error = self._dll.Picam_ReadParameterIntegerValue(camera, parameter.value, ctypes.byref(value))
        if error != PicamError.None_:
            print(PicamException(error))
        return value.value
    
    def ReadParameterFloatingPointValue(self, camera: PicamHandle, parameter: PicamParameter) -> float:
        """Read floating point parameter value"""
        value = piflt()
        error = self._dll.Picam_ReadParameterFloatingPointValue(camera, parameter.value, ctypes.byref(value))
        if error != PicamError.None_:
            print(PicamException(error))
        return value.value
    
    # Status Parameter Methods
    def CanWaitForStatusParameter(self, camera: PicamHandle, parameter: PicamParameter) -> bool:
        """Check if can wait for status parameter"""
        waitable = pibln()
        error = self._dll.Picam_CanWaitForStatusParameter(camera, parameter.value, ctypes.byref(waitable))
        if error != PicamError.None_:
            print(PicamException(error))
        return waitable.value
    
    def GetStatusParameterPurview(self, camera: PicamHandle, parameter: PicamParameter) -> PicamStatusPurview:
        """Get status parameter purview"""
        purview_ptr = POINTER(PicamStatusPurview)()
        error = self._dll.Picam_GetStatusParameterPurview(camera, parameter.value, ctypes.byref(purview_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(purview_ptr.contents)
        self._dll.Picam_DestroyStatusPurviews(purview_ptr)
        return result
    
    def EstimateTimeToStatusParameterValue(self, camera: PicamHandle, parameter: PicamParameter, value: int) -> int:
        """Estimate time to status parameter value"""
        estimated_time = piint()
        error = self._dll.Picam_EstimateTimeToStatusParameterValue(camera, parameter.value, value, ctypes.byref(estimated_time))
        if error != PicamError.None_:
            print(PicamException(error))
        return estimated_time.value
    
    def WaitForStatusParameterValue(self, camera: PicamHandle, parameter: PicamParameter, value: int, timeout: int):
        """Wait for status parameter value"""
        error = self._dll.Picam_WaitForStatusParameterValue(camera, parameter.value, value, timeout)
        if error != PicamError.None_:
            print(PicamException(error))
    
    # Parameter Information Methods
    def GetParameters(self, camera: PicamHandle) -> List[PicamParameter]:
        """Get available parameters for camera"""
        parameter_array_ptr = POINTER(piint)()
        count = piint()
        
        error = self._dll.Picam_GetParameters(camera, ctypes.byref(parameter_array_ptr), ctypes.byref(count))
        if error != PicamError.None_:
            print(PicamException(error))
        
        parameters = []
        for i in range(count.value):
            parameters.append(PicamParameter(parameter_array_ptr[i]))
        
        self._dll.Picam_DestroyParameters(parameter_array_ptr)
        return parameters
    
    def DoesParameterExist(self, camera: PicamHandle, parameter: PicamParameter) -> bool:
        """Check if parameter exists"""
        exists = pibln()
        error = self._dll.Picam_DoesParameterExist(camera, parameter.value, ctypes.byref(exists))
        if error != PicamError.None_:
            print(PicamException(error))
        return exists.value
    
    def IsParameterRelevant(self, camera: PicamHandle, parameter: PicamParameter) -> bool:
        """Check if parameter is relevant"""
        relevant = pibln()
        error = self._dll.Picam_IsParameterRelevant(camera, parameter.value, ctypes.byref(relevant))
        if error != PicamError.None_:
            print(PicamException(error))
        return relevant.value
    
    def GetParameterValueType(self, camera: PicamHandle, parameter: PicamParameter) -> PicamValueType:
        """Get parameter value type"""
        value_type = piint()
        error = self._dll.Picam_GetParameterValueType(camera, parameter.value, ctypes.byref(value_type))
        if error != PicamError.None_:
            print(PicamException(error))
        return PicamValueType(value_type.value)
    
    def GetParameterEnumeratedType(self, camera: PicamHandle, parameter: PicamParameter) -> PicamEnumeratedType:
        """Get parameter enumerated type"""
        enum_type = piint()
        error = self._dll.Picam_GetParameterEnumeratedType(camera, parameter.value, ctypes.byref(enum_type))
        if error != PicamError.None_:
            print(PicamException(error))
        return PicamEnumeratedType(enum_type.value)
    
    def GetParameterValueAccess(self, camera: PicamHandle, parameter: PicamParameter) -> PicamValueAccess:
        """Get parameter value access"""
        access = piint()
        error = self._dll.Picam_GetParameterValueAccess(camera, parameter.value, ctypes.byref(access))
        if error != PicamError.None_:
            print(PicamException(error))
        return PicamValueAccess(access.value)
    
    def GetParameterConstraintType(self, camera: PicamHandle, parameter: PicamParameter) -> PicamConstraintType:
        """Get parameter constraint type"""
        constraint_type = piint()
        error = self._dll.Picam_GetParameterConstraintType(camera, parameter.value, ctypes.byref(constraint_type))
        if error != PicamError.None_:
            print(PicamException(error))
        return PicamConstraintType(constraint_type.value)
    
    # Constraint Methods
    def GetParameterCollectionConstraint(self, camera: PicamHandle, parameter: PicamParameter, category: PicamConstraintCategory) -> PicamCollectionConstraint:
        """Get parameter collection constraint"""
        constraint_ptr = POINTER(PicamCollectionConstraint)()
        error = self._dll.Picam_GetParameterCollectionConstraint(camera, parameter.value, category.value, ctypes.byref(constraint_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(constraint_ptr.contents)
        self._dll.Picam_DestroyCollectionConstraints(constraint_ptr)
        return result
    
    def GetParameterRangeConstraint(self, camera: PicamHandle, parameter: PicamParameter, category: PicamConstraintCategory) -> PicamRangeConstraint:
        """Get parameter range constraint"""
        constraint_ptr = POINTER(PicamRangeConstraint)()
        error = self._dll.Picam_GetParameterRangeConstraint(camera, parameter.value, category.value, ctypes.byref(constraint_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(constraint_ptr.contents)
        self._dll.Picam_DestroyRangeConstraints(constraint_ptr)
        return result
    
    def GetParameterRoisConstraint(self, camera: PicamHandle, parameter: PicamParameter, category: PicamConstraintCategory) -> PicamRoisConstraint:
        """Get parameter ROIs constraint"""
        constraint_ptr = POINTER(PicamRoisConstraint)()
        error = self._dll.Picam_GetParameterRoisConstraint(camera, parameter.value, category.value, ctypes.byref(constraint_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(constraint_ptr.contents)
        self._dll.Picam_DestroyRoisConstraints(constraint_ptr)
        return result
    
    def GetParameterPulseConstraint(self, camera: PicamHandle, parameter: PicamParameter, category: PicamConstraintCategory) -> PicamPulseConstraint:
        """Get parameter pulse constraint"""
        constraint_ptr = POINTER(PicamPulseConstraint)()
        error = self._dll.Picam_GetParameterPulseConstraint(camera, parameter.value, category.value, ctypes.byref(constraint_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(constraint_ptr.contents)
        self._dll.Picam_DestroyPulseConstraints(constraint_ptr)
        return result
    
    def GetParameterModulationsConstraint(self, camera: PicamHandle, parameter: PicamParameter, category: PicamConstraintCategory) -> PicamModulationsConstraint:
        """Get parameter modulations constraint"""
        constraint_ptr = POINTER(PicamModulationsConstraint)()
        error = self._dll.Picam_GetParameterModulationsConstraint(camera, parameter.value, category.value, ctypes.byref(constraint_ptr))
        if error != PicamError.None_:
            print(PicamException(error))
        
        result = _copy_struct(constraint_ptr.contents)
        self._dll.Picam_DestroyModulationsConstraints(constraint_ptr)
        return result
    
    # Parameter Commitment Methods
    def AreParametersCommitted(self, camera: PicamHandle) -> bool:
        """Check if parameters are committed"""
        committed = pibln()
        error = self._dll.Picam_AreParametersCommitted(camera, ctypes.byref(committed))
        if error != PicamError.None_:
            print(PicamException(error))
        return committed.value
    
    def CommitParameters(self, camera: PicamHandle) -> List[PicamParameter]:
        """Commit parameters and return failed parameters"""
        failed_parameter_array_ptr = POINTER(piint)()
        count = piint()
        
        error = self._dll.Picam_CommitParameters(camera, ctypes.byref(failed_parameter_array_ptr), ctypes.byref(count))
        if error != PicamError.None_:
            print(PicamException(error))
        
        failed_parameters = []
        for i in range(count.value):
            failed_parameters.append(PicamParameter(failed_parameter_array_ptr[i]))
        
        self._dll.Picam_DestroyParameters(failed_parameter_array_ptr)
        return failed_parameters
    
    # Acquisition Methods
    def Acquire(self, camera: PicamHandle, readout_count: int, readout_timeout: int) -> Tuple[PicamAvailableData, PicamAcquisitionErrorsMask]:
        """Acquire data from camera"""
        available_data = PicamAvailableData()
        errors = piint()
        
        error = self._dll.Picam_Acquire(camera, readout_count, readout_timeout, ctypes.byref(available_data), ctypes.byref(errors))
        if error != PicamError.None_:
            print(PicamException(error))
        
        return available_data, PicamAcquisitionErrorsMask(errors.value)
    
    def StartAcquisition(self, camera: PicamHandle):
        """Start acquisition"""
        error = self._dll.Picam_StartAcquisition(camera)
        if error != PicamError.None_:
            print(PicamException(error))
    
    def StopAcquisition(self, camera: PicamHandle):
        """Stop acquisition"""
        error = self._dll.Picam_StopAcquisition(camera)
        if error != PicamError.None_:
            print(PicamException(error))
    
    def IsAcquisitionRunning(self, camera: PicamHandle) -> bool:
        """Check if acquisition is running"""
        running = pibln()
        error = self._dll.Picam_IsAcquisitionRunning(camera, ctypes.byref(running))
        if error != PicamError.None_:
            print(PicamException(error))
        return running.value
    
    def WaitForAcquisitionUpdate(self, camera: PicamHandle, readout_timeout: int) -> Tuple[PicamAvailableData, PicamAcquisitionStatus]:
        """Wait for acquisition update"""
        available_data = PicamAvailableData()
        status = PicamAcquisitionStatus()
        
        error = self._dll.Picam_WaitForAcquisitionUpdate(camera, readout_timeout, ctypes.byref(available_data), ctypes.byref(status))
        if error != PicamError.None_:
            print(PicamException(error))
        
        return available_data, status

# Exception Class
class PicamException(Exception):
    """Picam exception class"""
    def __init__(self, error_code):
        if isinstance(error_code, int):
            self.error_code = error_code
            self.error_name = PicamError(error_code).name
        else:
            self.error_code = error_code.value
            self.error_name = error_code.name
        super().__init__(f"Picam Error {self.error_code}: {self.error_name}")

def _copy_struct(src):
    """Deep-copy an SDK-owned structure (and its *_array/*_count arrays) before it is destroyed"""
    dst = type(src).from_buffer_copy(src)
    for name, ftype in src._fields_:
        if name.endswith('_array'):
            count = getattr(src, name[:-len('_array')] + '_count')
            setattr(dst, name, (ftype._type_ * count)(*getattr(src, name)[:count]))
        elif issubclass(ftype, Structure):
            setattr(dst, name, _copy_struct(getattr(src, name)))
    return dst

# Convenience Functions
def create_roi(x: int, y: int, width: int, height: int, x_binning: int = 1, y_binning: int = 1) -> PicamRoi:
    """Create a ROI structure"""
    return PicamRoi(x=x, y=y, width=width, height=height, x_binning=x_binning, y_binning=y_binning)

def create_pulse(delay: float, width: float) -> PicamPulse:
    """Create a pulse structure"""
    return PicamPulse(delay=delay, width=width)

def create_modulation(duration: float, frequency: float, phase: float, output_signal_frequency: float) -> PicamModulation:
    """Create a modulation structure"""
    return PicamModulation(duration=duration, frequency=frequency, phase=phase, output_signal_frequency=output_signal_frequency)