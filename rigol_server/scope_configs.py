scope1_config = {

    "ip": "192.168.1.114",

    "trig_channel": 1,
    "trig_level": 3.84,

    "timebase": 0.02,
    'time_offset': 0.098,

    "rms_window": 0.2,
    "rms_start": 0.005,

    "channels": {

        1: {
            "scale": 2.0,
            "offset": 0.0
        },
        2: {"scale": 0.5, "offset": -.56},

        3: {
            "scale": 0.1,
            "offset": -0.424
        },

        4: {
            "scale": 0.2,
            "offset": -.744
        }

    }
}

scope2_config = {

    "ip": "192.168.1.115",

    "trig_channel": 4,
    "trig_level": .4,
    'time_offset': 0.0,

    "timebase": 0.02,

    "rms_window": 0.16,
    "rms_start": -.29,

    "channels": {

        1: {"scale": 1.0, "offset": -2.2},
        2: {"scale": 0.5, "offset": 1.2},
        3: {"scale": 0.2, "offset": -.575},
        4: {"scale": 0.1, "offset": -.25}

    }
}