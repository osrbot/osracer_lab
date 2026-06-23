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
)


def hardware_summary():
    """Return a plain dict for scripts that need a serializable parameter source."""

    return {
        "chassis": OSRACER_CHASSIS,
        "camera_ar0234": OSRACER_CAMERA_AR0234,
        "lidar_25m": OSRACER_LIDAR_25M,
        "required_real_car_measurements": REQUIRED_REAL_CAR_MEASUREMENTS,
    }
