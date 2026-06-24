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


def lidar_25m_planar_scan_cfg(scan_rate_hz=10, angular_resolution_deg=0.25):
    """Return a conservative 2D scan model for sim2sim and replay checks."""

    lidar = OSRACER_LIDAR_25M
    if scan_rate_hz not in lidar["scan_rate_hz"]:
        raise ValueError(f"unsupported lidar scan_rate_hz: {scan_rate_hz}")
    if angular_resolution_deg not in lidar["angular_resolution_deg"]:
        raise ValueError(f"unsupported lidar angular_resolution_deg: {angular_resolution_deg}")
    horizontal_fov_deg = lidar["horizontal_fov_deg"]
    ray_count = int(round(horizontal_fov_deg / angular_resolution_deg)) + 1
    return {
        "horizontal_fov_deg": horizontal_fov_deg,
        "angular_resolution_deg": angular_resolution_deg,
        "scan_rate_hz": scan_rate_hz,
        "max_range_m": lidar["range_m_at_70pct_reflectivity"],
        "min_range_m": 0.05,
        "ray_count": ray_count,
        "frame_id": lidar["ros_frame_id"],
    }


OSRACER_SOURCE_AUTHORITY = {
    "firmware_repo": "https://github.com/osrbot/osrcore",
    "firmware_expected_branch": "main",
    "upper_computer_repo": "https://github.com/osrbot/osracer/tree/feat-demo",
    "upper_computer_expected_branch": "feat-demo",
    "firmware_protocol_doc": "docs/serial_protocol.md",
}

OSRACER_REAL_RUNTIME = {
    "ros_distro": "humble",
    "jetson_os": "JetPack 6.x / Ubuntu 22.04",
    "chassis_launch": "osracer_bringup chassis_ackermann.launch.py",
    "serial_port": "/dev/osrbot_base",
    "serial_baud": 460800,
    "command_protocol": "v <speed_mps> <steering_deg>",
    "command_watchdog_timeout_s": 0.5,
    "firmware_version_timeout_s": 0.8,
    "cmd_vel_topic": "/cmd_vel",
    "ackermann_cmd_topic": "/ackermann_cmd",
    "imu_topic": "/imu_filter",
    "odom_topic": "/odometry/filtered",
    "raw_mag_topic": "/magnetometer_data",
    "rc_topic": "/rc_data",
    "imu_serial_frame": "i qx qy qz qw ax ay az gx gy gz",
    "odom_serial_frame": "o px py pz vx vy vz yaw",
    "safety_note": "ESP32 firmware handles serial timeout and SBUS fallback; ROS also clamps steering.",
    "firmware_version_note": "ROS chassis startup queries fw version and logs OSRCORE ProjectVer when supported.",
}

OSRACER_FIRMWARE_CONTROL = {
    "source": "osrcore main/config.h, sdkconfig.defaults, docs/serial_protocol.md",
    "firmware_head_read": "729a6c2",
    "encoder": {
        "gpio_a": 3,
        "gpio_b": 9,
        "ppr": 1024,
        "gear_ratio": 10.55,
        "firmware_wheel_radius_m": 0.0425,
        "speed_calc_interval_ms": 20,
        "odom_scale_default": 1.0,
        "odom_scale_range": (0.5, 1.5),
    },
    "speed_control": {
        "control_interval_ms": 20,
        "pid_kp": 425.0,
        "pid_ki": 8.4,
        "pid_kd": 20.6,
        "pid_max_integral": 1000.0,
        "pid_deadband_mps": 0.05,
        "speed_lpf_alpha": 0.15,
        "odom_speed_lpf_alpha": 0.95,
        "max_speed_forward_mps": 6.0,
        "max_speed_reverse_mps": -6.0,
        "speed_stop_threshold_mps": 0.05,
        "throttle_feedforward_deadband_default_us": 90,
        "throttle_feedforward_deadband_range_us": (0, 300),
        "throttle_feedforward_max_us": 500,
    },
    "pwm": {
        "frequency_hz": 50,
        "resolution_bits": 14,
        "throttle_us": (1000, 1500, 2000),
        "steering_us": (1000, 1500, 2000),
        "steering_max_angle_deg": 30.0,
        "steering_trim_default_deg": 0.0,
        "steering_trim_range_deg": (-5.0, 5.0),
        "steering_reverse": True,
        "throttle_reverse": False,
    },
    "sbus": {
        "baud": 100000,
        "format": "8E2 inverted Futaba SBUS",
        "frame_len": 25,
        "range": (240, 1810),
        "steering_channel": 0,
        "throttle_channel": 2,
        "control_mode_channel": 6,
        "speed_mode_channel": 7,
        "reduced_speed_scale": 0.15,
    },
    "imu": {
        "model": "QMI8658",
        "address": "0x6B",
        "accel_range_g": 4,
        "gyro_range_dps": 1024,
        "odr_hz": 1000,
        "avg_samples": 5,
        "gyro_bias_samples": 100,
        "heater_target_c": 56.0,
        "heater_warm_c": 38.0,
        "heater_stable_c": 54.0,
        "heater_ready_timeout_ms": 300000,
    },
    "battery": {
        "low_voltage_threshold_v": 10.8,
        "low_voltage_recover_v": 11.1,
        "confirm_ms": 3000,
        "recover_ms": 3000,
    },
    "telemetry_intervals_ms": {
        "sync": 5,
        "legacy_imu": 5,
        "legacy_odom": 20,
        "mag": 50,
        "rc": 100,
        "battery": 2000,
        "serial_timeout": 500,
    },
}

OSRACER_SENSOR_EXTRINSICS = {
    "base_footprint_to_base_link_static_tf_xyz_rpy": (0.0, 0.0, 0.055, 0.0, 0.0, 0.0),
    "urdf_base_link_to_camera_link_xyz_rpy": (0.12323, -0.017229, -0.053395, -1.5708, 0.0, -1.5708),
    "static_tf_base_link_to_camera_link_xyz_rpy": (0.30, 0.0, 0.075, 0.0, 0.0, 0.0),
    "urdf_base_link_to_laser_xyz_rpy": (-0.082558, -0.017229, 0.034095, 0.0, 0.0, 0.0),
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
    "camera_intrinsics_fx_fy_cx_cy_distortion",
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
        "lidar_planar_scan_cfg": lidar_25m_planar_scan_cfg(),
        "source_authority": OSRACER_SOURCE_AUTHORITY,
        "real_runtime": OSRACER_REAL_RUNTIME,
        "firmware_control": OSRACER_FIRMWARE_CONTROL,
        "sensor_extrinsics": OSRACER_SENSOR_EXTRINSICS,
        "required_real_car_measurements": REQUIRED_REAL_CAR_MEASUREMENTS,
    }
