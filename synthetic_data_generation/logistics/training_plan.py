import datetime
import pandas as pd
from datetime import datetime, timedelta
import random
import numpy as np

# Random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_annual_training_plan(athlete, start_date= None, include_races=True):
    """Generates a structured annual training plan based on athlete profile."""
    
    age = athlete['age']
    vo2max = athlete['vo2max']
    training_experience = athlete['training_experience']
    recovery_rate = athlete['recovery_rate']
    weekly_hours = athlete['weekly_training_hours']
    ftp = athlete['ftp']
    weight = athlete['weight']
    W_per_kilo = ftp / weight
    specialization = athlete['specialization']

    ability_level = calculate_athlete_ability(training_experience, age, vo2max, weekly_hours, W_per_kilo)
    exp_levels = {
        'beginner': 1,
        'intermediate': 2,
        'advanced': 3,
        'elite': 4
    }
    
    exp_level = exp_levels.get(ability_level.lower(), 2)

    if start_date is None:
        start_date = datetime(2024, 1, 1)

    # Generate race schedule if races are included
    race_dates = []
    if include_races:
        # Number of races based on experience
        num_races = {
            1: random.randint(1, 2),    # Beginners: 1-2 races
            2: random.randint(2, 4),    # Intermediate: 2-4 races
            3: random.randint(3, 6),    # Advanced: 3-6 races
            4: random.randint(5, 8)     # Elite: 5-8 races
        }[exp_level]
        
        # Generate race dates (more likely in summer months)
        year = start_date.year
        month_weights = [0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.2, 0.15, 0.1, 0.02, 0.0, 0.0]
        
        for _ in range(num_races):
            # Select month with weighted probability
            month = random.choices(range(1, 13), weights=month_weights)[0]
            
            # Select day in month
            max_day = 28 if month == 2 else 30 if month in [4, 6, 9, 11] else 31
            day = random.randint(1, max_day)
            
            race_date = datetime(year, month, day)
            
            # Ensure we don't have races too close together (at least 3 weeks apart)
            if all(abs((race_date - existing_date).days) >= 21 for existing_date in race_dates):
                race_dates.append(race_date)
    
    # Sort race dates
    race_dates.sort()

    # Create phases based on race schedule
    phases = []
    if include_races and race_dates:
        # Start with base phase
        current_date = start_date
        for race_date in race_dates:
            # Calculate days until race
            days_until_race = (race_date - current_date).days
            
            if days_until_race > 120:  # If more than 4 months until race
                # Base phase (40-50% of time until race)
                base_duration = int(days_until_race * (0.4 + 0.1 * random.random()))
                phases.append({
                    'name': 'Base',
                    'start_date': current_date,
                    'end_date': current_date + timedelta(days=base_duration),
                    'tss_factor': 0.8
                })
                current_date += timedelta(days=base_duration)
                
                # Build phase (30-40% of time until race)
                build_duration = int(days_until_race * (0.3 + 0.1 * random.random()))
                remaining_build_days = build_duration  # Track the total duration left
                while remaining_build_days > 0:
                    is_deload_week = (remaining_build_days // 7 + 1) % 4 == 0  # Every 4th week is a deload week
                    
                    # Determine the duration of this phase (either 7 days or remaining days if it's the last week)
                    week_duration = min(7, remaining_build_days)

                    phases.append({
                        'name': 'Build',
                        'start_date': current_date,
                        'end_date': current_date + timedelta(days=week_duration - 1),
                        'tss_factor': 0.7 if is_deload_week else 1.0
                    })

                    # Move forward in time
                    current_date += timedelta(days=week_duration)
                    remaining_build_days -= week_duration
                
                # Peak phase (10-15% of time until race)
                peak_duration = int(days_until_race * (0.1 + 0.05 * random.random()))
                remaining_peak_days = peak_duration
                while remaining_peak_days > 0:
                    is_deload_week = (remaining_peak_days // 7 + 1) % 4 == 0
                    week_duration = min(7, remaining_peak_days)

                    phases.append({
                        'name': 'Peak',
                        'start_date': current_date,
                        'end_date': current_date + timedelta(days=week_duration - 1),
                        'tss_factor': 0.7 if is_deload_week else 1.1
                    })
                    current_date += timedelta(days=week_duration)
                    remaining_peak_days -= week_duration
            
            elif days_until_race > 60:  # If 2-4 months until race
                # Shorter base phase
                base_duration = int(days_until_race * 0.4)
                phases.append({
                    'name': 'Base',
                    'start_date': current_date,
                    'end_date': current_date + timedelta(days=base_duration),
                    'tss_factor': 0.85
                })
                current_date += timedelta(days=base_duration)
                
                # Build phase
                build_duration = int(days_until_race * 0.4)
                remaining_build_days = build_duration
                while remaining_build_days > 0:
                    is_deload_week = (remaining_build_days // 7 + 1) % 4 == 0
                    week_duration = min(7, remaining_build_days)

                    phases.append({
                        'name': 'Build',
                        'start_date': current_date,
                        'end_date': current_date + timedelta(days=week_duration - 1),
                        'tss_factor': 0.8 if is_deload_week else 1.1
                    })
                    current_date += timedelta(days=week_duration)
                    remaining_build_days -= week_duration
            
            else:  # Less than 2 months until race
                # Maintenance and pre-race prep
                prep_duration = max(7, days_until_race - 14)
                remaining_prep_days = prep_duration
                while remaining_prep_days > 0:
                    is_deload_week = (remaining_prep_days // 7 + 1) % 4 == 0
                    week_duration = min(7, remaining_prep_days)
                    
                    phases.append({
                        'name': 'Race Prep',
                        'start_date': current_date,
                        'end_date': current_date + timedelta(days=week_duration - 1),
                        'tss_factor': 0.8 if is_deload_week else 1.1
                    })
                    current_date += timedelta(days=week_duration)
                    remaining_prep_days -= week_duration
            
            # Taper phase (2 weeks before race)
            phases.append({
                'name': 'Taper',
                'start_date': current_date,
                'end_date': race_date - timedelta(days=1),
                'tss_factor': 0.7
            })
            
            # Race day
            phases.append({
                'name': 'Race',
                'start_date': race_date,
                'end_date': race_date,
                'tss_factor': 1.5  # Race day has high TSS
            })
            
            # Recovery phase (1-2 weeks after race depending on experience and race type)
            recovery_days = int(14 - 3 * recovery_rate)  # Faster recoverers need less time
            phases.append({
                'name': 'Recovery',
                'start_date': race_date + timedelta(days=1),
                'end_date': race_date + timedelta(days=recovery_days),
                'tss_factor': 0.5
            })
            
            current_date = race_date + timedelta(days=recovery_days + 1)
    
    # If there are no races or we need to fill the year after the last race
    end_of_year = datetime(start_date.year, 12, 31)
    if not phases or phases[-1]['end_date'] < end_of_year:
        current_date = start_date if not phases else phases[-1]['end_date'] + timedelta(days=1)
        
        while current_date <= end_of_year:
            # Alternate between base and build phases with recovery weeks
            for phase_name, phase_duration, tss_factor in [
                ('Off-season', 28, 0.7),
                ('Base', 42, 0.8),
                ('Build', 28, 1.0),
                ('Recovery', 7, 0.6)
            ]:
                phase_end = current_date + timedelta(days=phase_duration - 1)
                if phase_end > end_of_year:
                    phase_end = end_of_year
                
                phases.append({
                    'name': phase_name,
                    'start_date': current_date,
                    'end_date': phase_end,
                    'tss_factor': tss_factor
                })
                
                current_date = phase_end + timedelta(days=1)
                if current_date > end_of_year:
                    break

    # Generate detailed training plan based on phases
    plan_data = []

    base_weekly_tss = weekly_hours * random.uniform(40, 50) if exp_level == 1 else \
            weekly_hours * random.uniform(50, 65) if exp_level == 2 else \
            weekly_hours * random.uniform(65, 80) if exp_level == 3 else \
            weekly_hours * random.uniform(80, 90)
    
    # Maximum TSS per day based on experience
    max_daily_tss = {
        1: base_weekly_tss * 0.3,  # Beginners should avoid very high load days
        2: base_weekly_tss * 0.35,
        3: base_weekly_tss * 0.4,
        4: base_weekly_tss * 0.45   # Elites can handle higher single-day loads
    }[exp_level]
    
    # Day-of-week TSS distribution (Mon-Sun)
    # More training on weekends, less on Mon/Fri for typical schedule
    dow_tss_factor = [0.8, 1.0, 1.1, 1.0, 0.7, 1.2, 1.3]
    
    # Sport distribution (swim, bike, run, strength, rest) more focus on weakness but most volume on bike to minimize injury
    if specialization == 'bike_strong':
        sport_distribution = {
            'swim': 0.25,
            'bike': 0.4,
            'run': 0.3,
            'strength': 0.05,
            'rest': 0.0
        }
    elif specialization == 'run_strong':
        sport_distribution = {
            'swim': 0.3,
            'bike': 0.5,
            'run': 0.15,
            'strength': 0.05,
            'rest': 0.0
        }
    elif specialization == 'swim_strong':
        sport_distribution = {
            'swim': 0.1,
            'bike': 0.55,
            'run': 0.33,
            'strength': 0.05,
            'rest': 0.0
        }
    else:
        sport_distribution = {
            'swim': 0.2,
            'bike': 0.5,
            'run': 0.25,
            'strength': 0.05,
            'rest': 0.0  # Rest days will be calculated separately
        }
    
    # Generate detailed day plan for each phase
    current_date = start_date
    end_date = datetime(start_date.year, 12, 31)
    
    while current_date <= end_date:
        # Find current phase
        current_phase = None
        for phase in phases:
            if phase['start_date'] <= current_date <= phase['end_date']:
                current_phase = phase
                break
        
        if current_phase is None:
            # This shouldn't happen with properly structured phases
            # But add a default if somehow we're between phases
            current_phase = {
                'name': 'Transition',
                'tss_factor': 0.7
            }
        
        # Calculate base TSS target for this day
        day_of_week = current_date.weekday()  # 0-6 for Mon-Sun
        
        # Special handling for race days
        if current_phase['name'] == 'Race':
            # Race day - assign high TSS based on experience level
            daily_tss = {
                1: 150,  # Sprint distance for beginners
                2: 200,  # Olympic distance for intermediate 
                3: 300,  # Half-Ironman for advanced
                4: 450   # Full Ironman for elite
            }[exp_level]
            
            # Add some randomness
            daily_tss = daily_tss * (0.9 + 0.2 * random.random())
            
            # Assign all TSS to the racing sports
            sports = {
                'swim': 0.1,
                'bike': 0.6,
                'run': 0.3,
                'strength': 0,
                'rest': 0
            }
        else:
            # Normal training day
            daily_tss_base = (base_weekly_tss / 7) * current_phase['tss_factor'] * dow_tss_factor[day_of_week]
            
            # Add variability
            variability = 0.2  # 20% random variation
            daily_tss = daily_tss_base * (1 - variability/2 + variability * random.random())
            
            # Cap at max daily TSS
            daily_tss = min(daily_tss, max_daily_tss)
            
            # Decide if this is a rest day (more likely on Mondays and Fridays)
            rest_probability = 0.05  # Base probability
            if day_of_week == 0 or day_of_week == 4:  # Monday or Friday
                rest_probability = 0.2
            
            # Recovery weeks have more rest days
            if current_phase['name'] == 'Recovery' or current_phase['name'] == 'Taper':
                rest_probability *= 2
            
            # Determine if it's a rest day
            is_rest_day = random.random() < rest_probability
            
            if is_rest_day:
                sports = {
                    'swim': 0,
                    'bike': 0,
                    'run': 0,
                    'strength': 0,
                    'rest': 1.0
                }
                daily_tss = 0
            else:
                # Determine number of activities for the day
                if current_phase['name'] in ['Recovery', 'Taper']:
                    num_activities = random.choices([1, 2], weights=[0.7, 0.3])[0]
                else:
                    num_activities = random.choices([1, 2, 3], weights=[0.5, 0.3, 0.2])[0]
                
                # Initialize sports dictionary
                sports = {
                    'swim': 0,
                    'bike': 0,
                    'run': 0,
                    'strength': 0,
                    'rest': 0
                }
                
                # Base distribution from sport_distribution
                available_sports = ['swim', 'bike', 'run', 'strength']
                weights = [sport_distribution[sport] for sport in available_sports]
                
                # Modify weights based on training phase
                if current_phase['name'] == 'Base':
                    weights[1] *= 1.2  # More bike volume in base
                    weights[2] *= 0.8  # Less run volume in base

                # Ensure strength is not chosen if TSS is high and only one activity is planned
                if daily_tss > 80 and num_activities == 1:
                    available_sports.remove('strength')
                    weights = [sport_distribution[sport] for sport in available_sports]  # Recalculate weights
                
                # Select activities for the day
                selected_activities = random.choices(available_sports, weights=weights, k=num_activities)
                
                # Distribute load among selected activities
                total_weight = sum(sport_distribution[sport] for sport in selected_activities)
                for activity in selected_activities:
                    sports[activity] = sport_distribution[activity] / total_weight
        # Calculate TSS for each sport
        sport_tss = {}
        for sport, factor in sports.items():
            sport_tss[sport] = round(daily_tss * factor)

        # Ensure strength_tss does not exceed 70
        if sport_tss['strength'] > 70:
            sport_tss['strength'] = 70


        # Fix rounding errors: Adjust sum to match total TSS
        tss_diff = round(daily_tss) - sum(sport_tss.values())

        if tss_diff != 0:
            # Find the sport with the maximum TSS and adjust it
            max_sport = max(sport_tss, key=sport_tss.get)
            sport_tss[max_sport] += tss_diff
        
        # Add to plan data
        plan_data.append({
            'date': current_date,
            'day_of_week': current_date.strftime('%A'),
            'phase': current_phase['name'],
            'total_tss': round(daily_tss),
            'swim_tss': sport_tss['swim'],
            'bike_tss': sport_tss['bike'],
            'run_tss': sport_tss['run'],
            'strength_tss': sport_tss['strength'],
            'is_rest_day': sports['rest'] > 0.5,
            'is_race_day': current_phase['name'] == 'Race'
        })
        
        # Move to next day
        current_date += timedelta(days=1)
    
    # Convert to DataFrame
    plan_df = pd.DataFrame(plan_data)

    # Add week number column
    plan_df['week_number'] = ((plan_df['date'] - start_date).dt.days // 7) + 1
    
    # Calculate weekly totals
    weekly_totals = plan_df.groupby('week_number').agg({
        'total_tss': 'sum',
        'swim_tss': 'sum',
        'bike_tss': 'sum',
        'run_tss': 'sum',
        'strength_tss': 'sum'
    }).reset_index()
    
    # Check if weekly totals respect 10% rule
    adjusted_weekly_totals = apply_progressive_overload_rule(weekly_totals, athlete['weekly_training_hours'])
    
    # Apply the adjusted weekly totals back to the daily plan
    for week in adjusted_weekly_totals.itertuples():
        week_idx = week.week_number
        
        # Calculate adjustment factor
        if weekly_totals.loc[weekly_totals['week_number'] == week_idx, 'total_tss'].values[0] > 0:
            adj_factor = week.total_tss / weekly_totals.loc[weekly_totals['week_number'] == week_idx, 'total_tss'].values[0]
        else:
            adj_factor = 1.0
        
        # Apply adjustment to each day in the week
        mask = plan_df['week_number'] == week_idx
        plan_df.loc[mask, 'total_tss'] = (plan_df.loc[mask, 'total_tss'] * adj_factor).round()
        plan_df.loc[mask, 'swim_tss'] = (plan_df.loc[mask, 'swim_tss'] * adj_factor).round()
        plan_df.loc[mask, 'bike_tss'] = (plan_df.loc[mask, 'bike_tss'] * adj_factor).round()
        plan_df.loc[mask, 'run_tss'] = (plan_df.loc[mask, 'run_tss'] * adj_factor).round()
        plan_df.loc[mask, 'strength_tss'] = (plan_df.loc[mask, 'strength_tss'] * adj_factor).round()

    detailed_plan = add_workout_details(plan_df, athlete)
    
    return detailed_plan, race_dates

def apply_progressive_overload_rule(weekly_totals, weekly_hours):
    """Apply the 10% progressive overload rule and ensure weekly TSS matches athlete's indicated hours"""
    
    # Calculate target weekly TSS based on athlete's indicated hours
    # Using an average conversion factor of 60-70 TSS per hour
    target_weekly_tss = weekly_hours * 65
    
    # Start with a base TSS that's lower than the target to allow for progression
    starting_tss = target_weekly_tss * 0.7
    
    # Initialize the first week
    adjusted_totals = weekly_totals.copy()
    adjusted_totals.loc[0, 'total_tss'] = int(round(starting_tss))
    
    # Apply 10% rule to subsequent weeks (except recovery/taper weeks)
    for i in range(1, len(weekly_totals)):
        prev_week_tss = adjusted_totals.loc[i-1, 'total_tss']
        current_week_tss = weekly_totals.loc[i, 'total_tss']
        
        # Check if this is a recovery/taper week (significantly lower TSS than previous week)
        is_recovery_week = current_week_tss < prev_week_tss * 0.8
        
        if is_recovery_week:
            # Keep recovery weeks at 60-70% of previous week
            adjusted_totals.loc[i, 'total_tss'] = int(round(prev_week_tss * 0.65))
        else:
            # Apply 10% rule for normal progression weeks
            max_allowed_tss = prev_week_tss * 1.1
            
            # Cap at target TSS based on athlete's weekly hours
            max_allowed_tss = min(max_allowed_tss, target_weekly_tss * 1.05)
            
            # Set the adjusted value
            if current_week_tss > max_allowed_tss:
                adjusted_totals.loc[i, 'total_tss'] = int(round(max_allowed_tss))
    
    # Adjust distribution across disciplines proportionally
    for i in range(len(weekly_totals)):
        if weekly_totals.loc[i, 'total_tss'] > 0:
            adj_factor = adjusted_totals.loc[i, 'total_tss'] / weekly_totals.loc[i, 'total_tss']
            
            adjusted_totals.loc[i, 'swim_tss'] = (weekly_totals.loc[i, 'swim_tss'] * adj_factor).round()
            adjusted_totals.loc[i, 'bike_tss'] = (weekly_totals.loc[i, 'bike_tss'] * adj_factor).round()
            adjusted_totals.loc[i, 'run_tss'] = (weekly_totals.loc[i, 'run_tss'] * adj_factor).round()
            adjusted_totals.loc[i, 'strength_tss'] = (weekly_totals.loc[i, 'strength_tss'] * adj_factor).round()
    
    return adjusted_totals

def add_workout_details(training_plan, athlete_profile):
    """
    Add specific workout details to each day in the training plan.
    
    Parameters:
    -----------
    training_plan : pd.DataFrame
        DataFrame with daily training targets
    athlete_profile : dict
        Dictionary containing athlete attributes
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with detailed workout information added
    """
    # Extract athlete metrics
    ftp = athlete_profile['ftp']
    max_hr = athlete_profile['max_hr']
    css = athlete_profile['css']

    # Define intensity percentages per phase
    phase_intensity_distribution = {
        'Base': (90, 10),
        'Build': (80, 20),
        'Peak': (70, 30),
        'Race Prep': (75, 25),
        'Race': (100, 0),
        'Taper': (85, 15),
        'Off-season': (90, 10),
        'Recovery': (100, 0)  # No high-intensity in recovery weeks
    }
    
    # Create workout zones
    hr_zones = {
        1: (0.5 * max_hr, 0.6 * max_hr),  # Recovery
        2: (0.6 * max_hr, 0.7 * max_hr),  # Endurance
        3: (0.7 * max_hr, 0.8 * max_hr),  # Tempo
        4: (0.8 * max_hr, 0.9 * max_hr),  # Threshold
        5: (0.9 * max_hr, max_hr)         # VO2max/Anaerobic
    }
    
    power_zones = {
        1: (0.55 * ftp, 0.75 * ftp),      # Recovery
        2: (0.75 * ftp, 0.9 * ftp),       # Endurance
        3: (0.9 * ftp, 1.05 * ftp),       # Tempo
        4: (1.05 * ftp, 1.2 * ftp),       # Threshold
        5: (1.2 * ftp, 1.5 * ftp)         # VO2max/Anaerobic
    }
    
    # Swimming speeds based on experience (in seconds per 100m)
    swim_zones = {
        1: (1.1 * css, 1.2 * css),  # Easy/Recovery
        2: (1.02 * css, 1.09 * css),  # Steady/Endurance
        3: (0.98 * css, 1.01 * css),  # Threshold
        4: (0.9 * css, 0.97 * css),  # Fast/Interval
        5: (0.85 * css, 0.9 * css)  # Sprint
    }
    
    # Define workout templates for each sport
    swim_workouts = {
        'recovery': {
            'name': 'Easy Swim',
            'description': 'Easy technique-focused swim with drills',
            'zones': [swim_zones[1], swim_zones[2]],
            'tss_per_hour': 25
        },
        'endurance': {
            'name': 'Endurance Swim',
            'description': 'Steady-paced endurance swim with some drill sets',
            'zones': [swim_zones[2]],
            'tss_per_hour': 50
        },
        'intervals': {
            'name': 'Swim Intervals',
            'description': 'Mixed intervals focusing on speed and technique',
            'zones': [swim_zones[3], swim_zones[4]],
            'tss_per_hour': 90
        },
        'threshold': {
            'name': 'Threshold Swim',
            'description': 'Sustained effort at or near threshold pace',
            'zones': [swim_zones[4]],
            'tss_per_hour': 80
        },
        'speed': {
            'name': 'Speed Work',
            'description': 'Short, high-intensity repeats with full recovery',
            'zones': [swim_zones[4], swim_zones[5]],
            'tss_per_hour': 100
        }
    }
    
    bike_workouts = {
        'recovery': {
            'name': 'Recovery Ride',
            'description': 'Very easy spinning to promote recovery',
            'zones': [power_zones[1], power_zones[2]],
            'tss_per_hour': 30
        },
        'endurance': {
            'name': 'Endurance Ride',
            'description': 'Steady effort to build aerobic endurance',
            'zones': [power_zones[2]],
            'tss_per_hour': 40
        },
        'tempo': {
            'name': 'Tempo Ride',
            'description': 'Sustained moderate effort with some harder efforts',
            'zones': [power_zones[3]],
            'tss_per_hour': 60
        },
        'sweetspot': {
            'name': 'Sweet Spot Intervals',
            'description': 'Intervals at 88-93% of FTP',
            'zones': [power_zones[3], power_zones[4]],
            'tss_per_hour': 70
        },
        'threshold': {
            'name': 'Threshold Intervals',
            'description': 'Intervals at or just below FTP',
            'zones': [power_zones[4]],
            'tss_per_hour': 80
        },
        'vo2max': {
            'name': 'VO2max Intervals',
            'description': 'Short, high-intensity intervals',
            'zones': [power_zones[5]],
            'tss_per_hour': 100
        }
    }
    
    run_workouts = {
        'recovery': {
            'name': 'Recovery Run',
            'description': 'Very easy pace to promote recovery',
            'zones': [hr_zones[1], hr_zones[2]],
            'tss_per_hour': 30
        },
        'endurance': {
            'name': 'Endurance Run',
            'description': 'Steady effort to build aerobic endurance',
            'zones': [hr_zones[2]],
            'tss_per_hour': 50
        },
        'long': {
            'name': 'Long Run',
            'description': 'Extended duration at easy to moderate pace',
            'zones': [hr_zones[2]],
            'tss_per_hour': 50
        },
        'tempo': {
            'name': 'Tempo Run',
            'description': 'Sustained effort at moderate intensity',
            'zones': [hr_zones[3]],
            'tss_per_hour': 70
        },
        'threshold': {
            'name': 'Threshold Intervals',
            'description': 'Intervals at or near threshold pace',
            'zones': [hr_zones[4]],
            'tss_per_hour': 95
        },
        'intervals': {
            'name': 'Speed Intervals',
            'description': 'Short, high-intensity repeats with recovery',
            'zones': [hr_zones[4], hr_zones[5]],
            'tss_per_hour': 100
        }
    }
    
    strength_workouts = {
        'core': {
            'name': 'Core Strength',
            'description': 'Core-focused exercises to improve stability',
            'tss_per_hour': 40
        },
        'general': {
            'name': 'General Strength',
            'description': 'Full-body strength routine',
            'tss_per_hour': 50
        },
        'sport_specific': {
            'name': 'Sport-Specific Strength',
            'description': 'Strength exercises targeting swim/bike/run muscles',
            'tss_per_hour': 60
        },
        'plyometric': {
            'name': 'Plyometric Training',
            'description': 'Explosive exercises to build power',
            'tss_per_hour': 70
        }
    }
    
    # Create detailed workout plan
    detailed_plan = training_plan.copy()
    
    # Add workout details columns
    workout_detail_columns = [
        'swim_workout', 'swim_duration', 
        'bike_workout', 'bike_duration', 
        'run_workout', 'run_duration', 
        'strength_workout', 'strength_duration'
    ]
    
    for col in workout_detail_columns:
        detailed_plan[col] = None
    
    # Process each day
    for idx, day in detailed_plan.iterrows():
        # Skip rest days
        if day['is_rest_day']:
            continue
        phase = day['phase']
        low_intensity, high_intensity = phase_intensity_distribution[phase]

        def assign_workout(discipline, tss, workout_dict):
            if tss == 0:
                return None, 0

            intensity = select_intensity(tss, discipline)
            workout_weights = get_workout_weights(tss, intensity, discipline)
            workout_type = max(workout_weights, key=workout_weights.get)  

            workout = workout_dict[workout_type]
            duration_minutes = round((tss / workout['tss_per_hour']) * 60)

            return workout['name'], duration_minutes

        # Function to randomly assign intensity based on 80/20 principle
        def select_intensity(tss, discipline):
            if discipline == 'bike' and tss < 70:
                return "low"
            elif discipline == 'run' and tss < 80:
                return "low"
            elif discipline == 'swim' and tss < 60:
                return "low"
            elif discipline == 'swim' and tss > 70:
                return "high"
            else:
                return "low" if random.randint(1, 100) <= low_intensity else "high"
            
        # Handle each sport
        detailed_plan.at[idx, 'swim_workout'], detailed_plan.at[idx, 'swim_duration'] = assign_workout('swim', day['swim_tss'], swim_workouts)
        detailed_plan.at[idx, 'bike_workout'], detailed_plan.at[idx, 'bike_duration'] = assign_workout('bike', day['bike_tss'], bike_workouts)
        detailed_plan.at[idx, 'run_workout'], detailed_plan.at[idx, 'run_duration'] = assign_workout('run', day['run_tss'], run_workouts)

        # Strength
        if day['strength_tss'] > 0:
            # Select workout type based on TSS
            if day['strength_tss'] < 40:
                strength_workout_type = 'core'
            elif day['strength_tss'] < 50:
                 strength_workout_type = 'general'
            elif day['strength_tss'] < 60:
                 strength_workout_type = 'sport_specific'
            else:
                 strength_workout_type = 'plyometric'
            
            strength_workout = strength_workouts[strength_workout_type]
            
            # Calculate duration based on TSS
            strength_duration_hours = day['strength_tss'] / strength_workout['tss_per_hour']
            strength_duration_minutes = round(strength_duration_hours * 60)

            # Update plan
            detailed_plan.at[idx, 'strength_workout'] = strength_workout['name']
            detailed_plan.at[idx, 'strength_duration'] = strength_duration_minutes
    
    return detailed_plan
        

def calculate_athlete_ability(years_experience, age, vo2max, weekly_hours, ftp_kg):
    """Calculates an athlete's ability level based on multiple performance factors."""

    # Define scoring ranges
    score_ranges = {
        "experience": [(10, 20), (float("inf"), lambda x: min(20, x * 2))],
        "age": [(25, 8), (35, 10), (45, 7), (55, 6), (float("inf"), 3)],
        "vo2max": [(40, 5), (50, 10), (60, 15), (70, 20), (float("inf"), 25)],
        "weekly_hours": [(7, 5), (9, 10), (12, 15), (float("inf"), 20)],
        "ftp_kg": [(3, 5), (3.5, 10), (4.5, 15), (5.5, 20), (float("inf"), 25)],
    }

    # Helper function to get score from ranges
    def get_score(value, category):
        for threshold, score in score_ranges[category]:
            if value < threshold:
                return score(value) if callable(score) else score

    # Calculate individual scores
    experience_score = get_score(years_experience, "experience")
    age_score = get_score(age, "age")
    vo2max_score = get_score(vo2max, "vo2max")
    weekly_score = get_score(weekly_hours, "weekly_hours")
    ftp_score = get_score(ftp_kg, "ftp_kg")

    # Total Score Calculation
    total_score = sum([experience_score, age_score, vo2max_score, weekly_score, ftp_score])

    # Ability Level Categorization
    ability_levels = [(30, "Beginner"), (50, "Intermediate"), (75, "Advanced"), (float("inf"), "Elite")]
    ability_level = next(label for threshold, label in ability_levels if total_score <= threshold)

    return ability_level

def get_workout_weights(tss, intensity, discipline):
    """Get workout type weights based on TSS and intensity level."""
    
    if discipline == 'swim':
        if intensity == "low":
            if tss < 30:
                return {'recovery': 1}
            else:
                return {'recovery': 0.2, 'endurance': 0.8}
        else:
            if tss < 50:
                return {'threshold': 0.4, 'speed': 0.1, 'intervals': 0.5}
            elif tss > 100:
                return {'speed': 1}
            else:
                return {'threshold': 0.4, 'speed': 0.2, 'intervals': 0.4}
    
    elif discipline == 'bike':
        if intensity == "low":
            if tss < 30:
                return {'recovery': 1}
            else:
                return {'endurance': 1}
        else:
            if tss < 50:
                return {'tempo': 0.4, 'sweetspot': 0.3, 'threshold': 0.2, 'vo2max': 0.1}
            elif tss < 80:
                return {'tempo': 0.3, 'sweetspot': 0.4, 'threshold': 0.2, 'vo2max': 0.1}
            else:
                return {'tempo': 0.1, 'sweetspot': 0.3, 'threshold': 0.4, 'vo2max': 0.2}
    
    elif discipline == 'run':
        if intensity == "low":
            if tss <= 40:
                return {'recovery': 1, 'endurance': 0, 'long': 0}
            elif tss < 120:
                return {'recovery': 0, 'endurance': 1, 'long': 0}
            else:
                return {'recovery': 0, 'endurance': 0, 'long': 1}
        else:
            if tss < 50:
                return {'tempo': 0.4, 'threshold': 0.3, 'intervals': 0.2, 'hills': 0.1}
            elif tss < 80:
                return {'tempo': 0.3, 'threshold': 0.4, 'intervals': 0.2, 'hills': 0.1}
            else:
                return {'tempo': 0.2, 'threshold': 0.3, 'intervals': 0.3, 'hills': 0.2}