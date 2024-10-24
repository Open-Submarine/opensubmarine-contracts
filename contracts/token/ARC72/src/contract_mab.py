from algopy import UInt64, subroutine


##############################################
# function: calculate_mab_pure (internal)
# arguments:
# - now, timestamp
# - vesting_delay, how many periods in vesting
# - period_seconds, how many seconds in period
# - lockup delay, how many period in lockup
# - period, how many periods
# - funding, when funded
# - total, how much funded
# - distribution_count, how many periods in distribution
# - distribution_seconds, how many seconds in distribution
# purpose: calculate minimum allowable balance
# returns' minimum allowable balance
##############################################
@subroutine
def calculate_mab_pure(
    now: UInt64,
    vesting_delay: UInt64,
    period_seconds: UInt64,
    lockup_delay: UInt64,
    period: UInt64,
    funding: UInt64,
    total: UInt64,
    distribution_count: UInt64,
    distribution_seconds: UInt64,
) -> UInt64:
    lockup_periods = lockup_delay * period
    lockup_seconds = lockup_periods * period_seconds
    vesting_seconds = vesting_delay * period_seconds
    fully_vested = funding + vesting_seconds + lockup_seconds
    locked_up = now <= fully_vested
    if locked_up:
        return total
    else:  
        elapsed_periods = (now - fully_vested) // distribution_seconds
        if elapsed_periods <= distribution_count:
            return (
                total * (distribution_count - elapsed_periods)
            ) // distribution_count
        else:
            return UInt64(0)
