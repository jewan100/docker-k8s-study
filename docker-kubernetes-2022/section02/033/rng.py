from random import randint

min_number = int(input("Enter the minimum number: "))
max_number = int(input("Enter the maximum number: "))

if(max_number < min_number):
    print("Invalid range. Maximum should be greater than or equal to Minimum.")
else:
    random_number = randint(min_number, max_number)
    print(f"Random number between {min_number} and {max_number}: {random_number}")