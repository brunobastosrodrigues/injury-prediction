//! Parquet file output.

use anyhow::Result;
use arrow::array::*;
use arrow::datatypes::{DataType, Field, Schema};
use arrow::record_batch::RecordBatch;
use parquet::arrow::ArrowWriter;
use std::fs::File;
use std::path::Path;
use std::sync::Arc;

use crate::simulation::SimulationResult;
use crate::athlete::Athlete;
use crate::simulation::DailyMetrics;
use crate::activity::Activity;

/// Write all simulation results to Parquet files.
pub fn write_all(result: &SimulationResult, output_dir: &Path) -> Result<()> {
    std::fs::create_dir_all(output_dir)?;

    // Write athletes
    let athletes: Vec<_> = result.results.iter().map(|r| &r.athlete).collect();
    write_athletes(&athletes, &output_dir.join("athlete_profiles.parquet"))?;

    // Write daily metrics
    let daily_metrics: Vec<_> = result.results.iter()
        .flat_map(|r| &r.daily_metrics)
        .collect();
    write_daily_metrics(&daily_metrics, &output_dir.join("daily_data.parquet"))?;

    // Write activities
    let activities: Vec<_> = result.results.iter()
        .flat_map(|r| &r.activities)
        .collect();
    write_activities(&activities, &output_dir.join("activity_data.parquet"))?;

    // Write metadata
    write_metadata(result, output_dir)?;

    Ok(())
}

/// Write athlete profiles to Parquet.
fn write_athletes(athletes: &[&Athlete], path: &Path) -> Result<()> {
    let schema = Arc::new(Schema::new(vec![
        Field::new("athlete_id", DataType::Utf8, false),
        Field::new("gender", DataType::Utf8, false),
        Field::new("age", DataType::Int32, false),
        Field::new("height_cm", DataType::Float64, false),
        Field::new("weight_kg", DataType::Float64, false),
        Field::new("genetic_factor", DataType::Float64, false),
        Field::new("hrv_baseline", DataType::Float64, false),
        Field::new("max_hr", DataType::Float64, false),
        Field::new("resting_hr", DataType::Float64, false),
        Field::new("lthr", DataType::Float64, false),
        Field::new("vo2max", DataType::Float64, false),
        Field::new("ftp", DataType::Float64, false),
        Field::new("css", DataType::Float64, false),
        Field::new("run_threshold_pace", DataType::Float64, false),
        Field::new("training_experience", DataType::Int32, false),
        Field::new("weekly_training_hours", DataType::Float64, false),
        Field::new("recovery_rate", DataType::Float64, false),
        Field::new("specialization", DataType::Utf8, false),
        Field::new("lifestyle", DataType::Utf8, false),
        Field::new("sleep_time_norm", DataType::Float64, false),
        Field::new("sleep_quality", DataType::Float64, false),
        Field::new("nutrition_factor", DataType::Float64, false),
        Field::new("stress_factor", DataType::Float64, false),
        Field::new("smoking_factor", DataType::Float64, false),
        Field::new("drinking_factor", DataType::Float64, false),
        Field::new("sensor_profile", DataType::Utf8, false),
        Field::new("chronotype", DataType::Utf8, false),
    ]));

    let ids: StringArray = athletes.iter().map(|a| Some(a.id.as_str())).collect();
    let genders: StringArray = athletes.iter().map(|a| Some(a.gender.as_str())).collect();
    let ages: Int32Array = athletes.iter().map(|a| Some(a.age as i32)).collect();
    let heights: Float64Array = athletes.iter().map(|a| Some(a.height_cm)).collect();
    let weights: Float64Array = athletes.iter().map(|a| Some(a.weight_kg)).collect();
    let genetics: Float64Array = athletes.iter().map(|a| Some(a.genetic_factor)).collect();
    let hrv_baselines: Float64Array = athletes.iter().map(|a| Some(a.hrv_baseline)).collect();
    let max_hrs: Float64Array = athletes.iter().map(|a| Some(a.max_hr)).collect();
    let resting_hrs: Float64Array = athletes.iter().map(|a| Some(a.resting_hr)).collect();
    let lthrs: Float64Array = athletes.iter().map(|a| Some(a.lthr)).collect();
    let vo2maxs: Float64Array = athletes.iter().map(|a| Some(a.vo2max)).collect();
    let ftps: Float64Array = athletes.iter().map(|a| Some(a.ftp)).collect();
    let csss: Float64Array = athletes.iter().map(|a| Some(a.css)).collect();
    let paces: Float64Array = athletes.iter().map(|a| Some(a.run_threshold_pace)).collect();
    let experiences: Int32Array = athletes.iter().map(|a| Some(a.training_experience as i32)).collect();
    let hours: Float64Array = athletes.iter().map(|a| Some(a.weekly_training_hours)).collect();
    let recovery_rates: Float64Array = athletes.iter().map(|a| Some(a.recovery_rate)).collect();
    let specializations: StringArray = athletes.iter().map(|a| Some(a.specialization.as_str())).collect();
    let lifestyles: StringArray = athletes.iter().map(|a| Some(a.lifestyle.name.as_str())).collect();
    let sleep_norms: Float64Array = athletes.iter().map(|a| Some(a.lifestyle.sleep_hours)).collect();
    let sleep_quals: Float64Array = athletes.iter().map(|a| Some(a.lifestyle.sleep_quality)).collect();
    let nutritions: Float64Array = athletes.iter().map(|a| Some(a.lifestyle.nutrition)).collect();
    let stresses: Float64Array = athletes.iter().map(|a| Some(a.lifestyle.stress)).collect();
    let smokings: Float64Array = athletes.iter().map(|a| Some(a.lifestyle.smoking)).collect();
    let drinkings: Float64Array = athletes.iter().map(|a| Some(a.lifestyle.drinking)).collect();
    let sensors: StringArray = athletes.iter().map(|a| Some(a.sensor_profile.as_str())).collect();
    let chronotypes: StringArray = athletes.iter().map(|a| Some(a.chronotype.as_str())).collect();

    let batch = RecordBatch::try_new(
        schema.clone(),
        vec![
            Arc::new(ids),
            Arc::new(genders),
            Arc::new(ages),
            Arc::new(heights),
            Arc::new(weights),
            Arc::new(genetics),
            Arc::new(hrv_baselines),
            Arc::new(max_hrs),
            Arc::new(resting_hrs),
            Arc::new(lthrs),
            Arc::new(vo2maxs),
            Arc::new(ftps),
            Arc::new(csss),
            Arc::new(paces),
            Arc::new(experiences),
            Arc::new(hours),
            Arc::new(recovery_rates),
            Arc::new(specializations),
            Arc::new(lifestyles),
            Arc::new(sleep_norms),
            Arc::new(sleep_quals),
            Arc::new(nutritions),
            Arc::new(stresses),
            Arc::new(smokings),
            Arc::new(drinkings),
            Arc::new(sensors),
            Arc::new(chronotypes),
        ],
    )?;

    let file = File::create(path)?;
    let mut writer = ArrowWriter::try_new(file, schema, None)?;
    writer.write(&batch)?;
    writer.close()?;

    Ok(())
}

/// Write daily metrics to Parquet.
fn write_daily_metrics(metrics: &[&DailyMetrics], path: &Path) -> Result<()> {
    let schema = Arc::new(Schema::new(vec![
        Field::new("athlete_id", DataType::Utf8, false),
        Field::new("date", DataType::Utf8, false),
        Field::new("resting_hr", DataType::Float64, false),
        Field::new("hrv", DataType::Float64, false),
        Field::new("sleep_hours", DataType::Float64, false),
        Field::new("deep_sleep", DataType::Float64, false),
        Field::new("light_sleep", DataType::Float64, false),
        Field::new("rem_sleep", DataType::Float64, false),
        Field::new("sleep_quality", DataType::Float64, false),
        Field::new("body_battery_morning", DataType::Float64, false),
        Field::new("stress", DataType::Float64, false),
        Field::new("body_battery_evening", DataType::Float64, false),
        Field::new("planned_tss", DataType::Float64, false),
        Field::new("actual_tss", DataType::Float64, false),
        Field::new("ctl", DataType::Float64, false),
        Field::new("atl", DataType::Float64, false),
        Field::new("tsb", DataType::Float64, false),
        Field::new("acwr", DataType::Float64, false),
        Field::new("injury", DataType::Boolean, false),
        Field::new("injury_type", DataType::Utf8, true),
        Field::new("injury_probability", DataType::Float64, false),
    ]));

    let ids: StringArray = metrics.iter().map(|m| Some(m.athlete_id.as_str())).collect();
    let dates: StringArray = metrics.iter().map(|m| Some(m.date.to_string())).collect();
    let resting_hrs: Float64Array = metrics.iter().map(|m| Some(m.resting_hr)).collect();
    let hrvs: Float64Array = metrics.iter().map(|m| Some(m.hrv)).collect();
    let sleep_hours: Float64Array = metrics.iter().map(|m| Some(m.sleep_hours)).collect();
    let deep_sleeps: Float64Array = metrics.iter().map(|m| Some(m.deep_sleep)).collect();
    let light_sleeps: Float64Array = metrics.iter().map(|m| Some(m.light_sleep)).collect();
    let rem_sleeps: Float64Array = metrics.iter().map(|m| Some(m.rem_sleep)).collect();
    let sleep_quals: Float64Array = metrics.iter().map(|m| Some(m.sleep_quality)).collect();
    let batteries_am: Float64Array = metrics.iter().map(|m| Some(m.body_battery_morning)).collect();
    let stresses: Float64Array = metrics.iter().map(|m| Some(m.stress)).collect();
    let batteries_pm: Float64Array = metrics.iter().map(|m| Some(m.body_battery_evening)).collect();
    let planned: Float64Array = metrics.iter().map(|m| Some(m.planned_tss)).collect();
    let actual: Float64Array = metrics.iter().map(|m| Some(m.actual_tss)).collect();
    let ctls: Float64Array = metrics.iter().map(|m| Some(m.ctl)).collect();
    let atls: Float64Array = metrics.iter().map(|m| Some(m.atl)).collect();
    let tsbs: Float64Array = metrics.iter().map(|m| Some(m.tsb)).collect();
    let acwrs: Float64Array = metrics.iter().map(|m| Some(m.acwr)).collect();
    let injuries: BooleanArray = metrics.iter().map(|m| Some(m.injury)).collect();
    let injury_types: StringArray = metrics.iter().map(|m| m.injury_type.map(|t| t.as_str())).collect();
    let injury_probs: Float64Array = metrics.iter().map(|m| Some(m.injury_probability)).collect();

    let batch = RecordBatch::try_new(
        schema.clone(),
        vec![
            Arc::new(ids),
            Arc::new(dates),
            Arc::new(resting_hrs),
            Arc::new(hrvs),
            Arc::new(sleep_hours),
            Arc::new(deep_sleeps),
            Arc::new(light_sleeps),
            Arc::new(rem_sleeps),
            Arc::new(sleep_quals),
            Arc::new(batteries_am),
            Arc::new(stresses),
            Arc::new(batteries_pm),
            Arc::new(planned),
            Arc::new(actual),
            Arc::new(ctls),
            Arc::new(atls),
            Arc::new(tsbs),
            Arc::new(acwrs),
            Arc::new(injuries),
            Arc::new(injury_types),
            Arc::new(injury_probs),
        ],
    )?;

    let file = File::create(path)?;
    let mut writer = ArrowWriter::try_new(file, schema, None)?;
    writer.write(&batch)?;
    writer.close()?;

    Ok(())
}

/// Write activities to Parquet.
fn write_activities(activities: &[&Activity], path: &Path) -> Result<()> {
    let schema = Arc::new(Schema::new(vec![
        Field::new("athlete_id", DataType::Utf8, false),
        Field::new("date", DataType::Utf8, false),
        Field::new("sport", DataType::Utf8, false),
        Field::new("workout_type", DataType::Utf8, false),
        Field::new("duration_minutes", DataType::Float64, false),
        Field::new("tss", DataType::Float64, false),
        Field::new("intensity_factor", DataType::Float64, false),
        Field::new("avg_hr", DataType::Float64, true),
        Field::new("max_hr", DataType::Float64, true),
        Field::new("distance_km", DataType::Float64, true),
        Field::new("avg_speed_kph", DataType::Float64, true),
        Field::new("avg_power", DataType::Float64, true),
        Field::new("normalized_power", DataType::Float64, true),
        Field::new("avg_pace_min_km", DataType::Float64, true),
    ]));

    let ids: StringArray = activities.iter().map(|a| Some(a.athlete_id.as_str())).collect();
    let dates: StringArray = activities.iter().map(|a| Some(a.date.to_string())).collect();
    let sports: StringArray = activities.iter().map(|a| Some(a.sport.as_str())).collect();
    let types: StringArray = activities.iter().map(|a| Some(a.workout_type.as_str())).collect();
    let durations: Float64Array = activities.iter().map(|a| Some(a.duration_minutes)).collect();
    let tsss: Float64Array = activities.iter().map(|a| Some(a.tss)).collect();
    let ifs: Float64Array = activities.iter().map(|a| Some(a.intensity_factor)).collect();
    let avg_hrs: Float64Array = activities.iter().map(|a| a.avg_hr).collect();
    let max_hrs: Float64Array = activities.iter().map(|a| a.max_hr).collect();
    let distances: Float64Array = activities.iter().map(|a| a.distance_km).collect();
    let speeds: Float64Array = activities.iter().map(|a| a.avg_speed_kph).collect();
    let powers: Float64Array = activities.iter().map(|a| a.avg_power).collect();
    let nps: Float64Array = activities.iter().map(|a| a.normalized_power).collect();
    let paces: Float64Array = activities.iter().map(|a| a.avg_pace_min_km).collect();

    let batch = RecordBatch::try_new(
        schema.clone(),
        vec![
            Arc::new(ids),
            Arc::new(dates),
            Arc::new(sports),
            Arc::new(types),
            Arc::new(durations),
            Arc::new(tsss),
            Arc::new(ifs),
            Arc::new(avg_hrs),
            Arc::new(max_hrs),
            Arc::new(distances),
            Arc::new(speeds),
            Arc::new(powers),
            Arc::new(nps),
            Arc::new(paces),
        ],
    )?;

    let file = File::create(path)?;
    let mut writer = ArrowWriter::try_new(file, schema, None)?;
    writer.write(&batch)?;
    writer.close()?;

    Ok(())
}

/// Write metadata JSON file.
fn write_metadata(result: &SimulationResult, output_dir: &Path) -> Result<()> {
    let metadata = serde_json::json!({
        "n_athletes": result.results.len(),
        "n_daily_records": result.total_daily_records(),
        "n_activities": result.total_activities(),
        "injury_rate": result.injury_rate(),
    });

    let path = output_dir.join("metadata.json");
    let file = File::create(path)?;
    serde_json::to_writer_pretty(file, &metadata)?;

    Ok(())
}
