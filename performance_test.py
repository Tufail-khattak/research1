import matplotlib.pyplot as plt

# Data you collected from your tests (in milliseconds or microseconds)
# These values are placeholders - replace them with the actual values you collected.
request_counts = [1]  # For testing with one user

# Example times (replace with actual data collected from logs or browser console)
login_times = [21.1000]  # Replace with the actual login time (in milliseconds or microseconds)
validation_times = [13.5000]  # Replace with the actual session validation time (in milliseconds or microseconds)

# Plotting the data
plt.plot(request_counts, login_times, label='Login Time', color='green', marker='o')
plt.plot(request_counts, validation_times, label='Session Validation Time', color='blue', marker='o')

# Adding labels and title
plt.xlabel("Number of Requests (1 User)")  # X-axis label
plt.ylabel("Time Taken (Milliseconds)")  # Y-axis label
plt.title("Performance of ESID and TH for One User Request")  # Graph title
plt.legend()  # To show the labels
plt.grid(True)  # Show grid for better readability

# Show the plot
plt.show()
