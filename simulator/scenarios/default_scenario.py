def run_default_scenario(pallet_simulator, step_count):
    """
    A sample scenario: normal operation, then a traffic jam causes a problem.
    """
    # First 30 steps: Normal operation
    if step_count < 30:
        pallet_simulator.apply_scenario(cooling_efficiency=0.97, is_moving=True)

    # Steps 30-60: Traffic jam - truck is stopped, cooler is less effective
    elif 30 <= step_count < 60:
        pallet_simulator.apply_scenario(cooling_efficiency=0.85, is_moving=False)

    # After 60: Back to normal
    else:
        pallet_simulator.apply_scenario(cooling_efficiency=0.97, is_moving=True)
