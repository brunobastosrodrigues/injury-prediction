from simYear import generate_simulation_dataset, save_simulation_data

def main():
    # 1. Generate simulated data
    print("Generating simulation dataset...")
    simulated_data = generate_simulation_dataset(n_athletes=1)
    
    # 2. Save simulated data to CSV
    print("Saving simulated data to CSV...")
    save_simulation_data(simulated_data, output_folder="simulated_data")

if __name__ == "__main__":
    main()