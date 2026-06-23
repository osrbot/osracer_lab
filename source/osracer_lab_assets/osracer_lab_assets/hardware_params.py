"""Real OSRacer hardware parameters used to align sim2sim and sim2real work.

Keep unverified fields out of the simulation control path until they are measured
on the physical car. These constants are a shared reference for IsaacLab,
MuJoCo, Jetson runtime checks, and offline replay tooling.
"""

OSRACER_CHASSIS = {
    "wheelbase_m": 0.285,
    "rear_track_m": 0.235,
    "wheel_radius_m": 0.050,
    "simulation_max_speed_mps": 3.0,
    "simulation_max_steering_rad": 0.488,
    "initial_real_test_max_speed_mps": 0.3,
}

OSRACER_CAMERA_AR0234 = {
    "model": "DCXG200",
    "sensor": "AR0234",
    "shutter": "global",
    "lens_focal_length_mm": 2.7,
    "lens_distortion": "low_distortion",
    "advertised_fov_deg": 130.0,
    "resolution_px": (1920, 1200),
    "pixel_size_um": (3.0, 3.0),
    "frame_rate_fps": (90, 120),
    "interface": "USB2.0 UVC",
    "formats": ("MJPG", "YUY2"),
    "power_w": 2.0,
    "supply_v": 5.0,
    "module_size_mm": (36.0, 36.0),
    "net_weight_g": (59.9, 67.5),
    "ros_runtime": {
        "driver": "usb_cam",
        "device": "/dev/video0",
        "frame_id": "camera_link",
        "topic": "/rgb/image_raw",
        "configured_resolution_px": (640, 480),
        "configured_fps": 120.0,
        "pixel_format": "mjpeg2rgb",
    },
}


def ar0234_sensor_size_mm():
    """Return AR0234 active sensor size inferred from resolution and pixel pitch."""

    width_px, height_px = OSRACER_CAMERA_AR0234["resolution_px"]
    pixel_width_um, pixel_height_um = OSRACER_CAMERA_AR0234["pixel_size_um"]
    return (width_px * pixel_width_um / 1000.0, height_px * pixel_height_um / 1000.0)


def ar0234_pinhole_camera_cfg():
    """Return IsaacLab PinholeCameraCfg values derived from AR0234 sensor facts.

    The advertised 130 deg FOV is kept as a hardware note, but this pinhole
    approximation uses the physical focal length and active sensor size until
    checkerboard calibration provides fx/fy/cx/cy/distortion.
    """

    horizontal_aperture, vertical_aperture = ar0234_sensor_size_mm()
    return {
        "focal_length": OSRACER_CAMERA_AR0234["lens_focal_length_mm"],
        "horizontal_aperture": horizontal_aperture,
        "vertical_aperture": vertical_aperture,
        "clipping_range": (0.01, 100.0),
    }


OSRACER_LIDAR_25M = {
    "scan_type": "mechanical_rotating",
    "range_method": "pulse_tof",
    "horizontal_fov_deg": 270.0,
    "range_m_at_70pct_reflectivity": 25.0,
    "range_m_at_10pct_reflectivity": 15.0,
    "accuracy_m": 0.02,
    "angular_resolution_deg": (0.1, 0.25),
    "scan_rate_hz": (10, 20, 25, 30),
    "sample_rate_hz": (28800, 36000, 43200),
    "outputs": ("range", "angle", "intensity", "timestamp"),
    "transport": ("UDP/IP", "USB"),
    "wavelength_nm": 940,
    "laser_safety": "Class1",
    "size_mm": (60.0, 60.0, 80.0),
    "weight_g": 160.0,
    "power_w_max": 2.0,
    "supply_v": (9.0, 36.0),
    "ip_rating": "IP65",
    "ros_frame_id": "laser",
}

OSRACER_REAL_RUNTIME = {
    "chassis_launch": "osracer_bringup chassis_ackermann.launch.py",
    "serial_port": "/dev/osrbot_base",
    "serial_baud": 460800,
    "command_protocol": "v <speed_mps> <steering_deg>",
    "command_watchdog_timeout_s": 0.5,
    "cmd_vel_topic": "/cmd_vel",
    "ackermann_cmd_topic": "/ackermann_cmd",
    "imu_topic": "/imu_filter",
    "odom_topic": "/odometry/filtered",
    "raw_mag_topic": "/magnetometer_data",
    "rc_topic": "/rc_data",
    "imu_serial_frame": "i qx qy qz qw ax ay az gx gy gz",
    "odom_serial_frame": "o px py pz vx vy vz yaw",
    "safety_note": "ESP32 firmware handles serial timeout and SBUS fallback; ROS also clamps steering.",
}

OSRACER_SENSOR_EXTRINSICS = {
    "base_footprint_to_base_link_static_tf_xyz_rpy": (0.0, 0.0, 0.055, 0.0, 0.0, 0.0),
    "urdf_base_link_to_camera_link_xyz_rpy": (0.12323, -0.017229, -0.053395, -1.5708, 0.0, -1.5708),
    "static_tf_base_link_to_camera_link_xyz_rpy": (0.30, 0.0, 0.075, 0.0, 0.0, 0.0),
    "urdf_base_link_to_laser_xyz_rpy": (-0.082558, -0.017229, 0.034095, -0.00028339, -0.031729, 0.0057633),
    "static_tf_base_link_to_laser_xyz_rpy": (0.10, 0.0, 0.13, 0.0, 0.0, 0.0),
    "urdf_base_link_to_imu_link_xyz_rpy": (
        0.0417958953212156,
        -0.0177578126845364,
        -0.063598843109235,
        0.0,
        0.0,
        0.0,
    ),
    "static_tf_base_link_to_imu_link_xyz_rpy": (0.22, 0.0, 0.03, 0.0, 0.0, 0.0),
    "status": "URDF and robot_description_tf.launch.py disagree; measure and choose one source before calibrated sim2real.",
}

REQUIRED_REAL_CAR_MEASUREMENTS = (
    "full_vehicle_mass_kg_with_battery_jetson_sensors",
    "front_track_m",
    "tire_width_m",
    "front_rear_weight_distribution",
    "true_max_steering_rad_left_right",
    "steering_servo_pwm_min_center_max_or_protocol_units",
    "steering_response_time_s",
    "motor_kv_or_rated_rpm",
    "battery_voltage_s_count",
    "true_max_speed_mps",
    "minimum_stable_speed_mps",
    "throttle_deadband_and_response_delay_s",
    "encoder_ticks_per_revolution_and_mount_location",
    "imu_model_rate_ranges_and_frame_alignment",
    "camera_extrinsic_xyz_rpy_in_base_link",
    "lidar_extrinsic_xyz_rpy_in_base_link",
    "imu_extrinsic_xyz_rpy_in_base_link",
    "serial_baud_rate_and_command_latency_s",
    "sensor_timestamp_sync_method",
    "resolve_urdf_vs_static_tf_sensor_extrinsics",
)


def hardware_summary():
    """Return a plain dict for scripts that need a serializable parameter source."""

    return {
        "chassis": OSRACER_CHASSIS,
        "camera_ar0234": OSRACER_CAMERA_AR0234,
        "lidar_25m": OSRACER_LIDAR_25M,
        "camera_pinhole_cfg": ar0234_pinhole_camera_cfg(),
        "real_runtime": OSRACER_REAL_RUNTIME,
        "sensor_extrinsics": OSRACER_SENSOR_EXTRINSICS,
        "required_real_car_measurements": REQUIRED_REAL_CAR_MEASUREMENTS,
    }
