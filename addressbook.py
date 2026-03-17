import json
import os
import re


class Validator:
    """
    Utility class for strict data validation and sanitization.
    Static methods are used here so we can validate data without
    needing to create an instance of the class.
    """

    @staticmethod
    def validate_name(name):
        """
        Ensures name is not empty and contains no numerical digits.
        Raises ValueError if validation fails.
        """
        if any(char.isdigit() for char in name):
            raise ValueError("Names cannot contain numbers.")
        if not name.strip():
            raise ValueError("Name cannot be empty.")
        return name.strip()

    @staticmethod
    def format_phone(phone_str):
        """
        Checks for illegal symbols, strips formatting, and ensures 10 digits.
        Returns phone in standardized XXX-XXX-XXXX format.
        """
        # Regex check: only allow digits, spaces, hyphens, and parentheses
        if re.search(r"[^\d\s\-\(\)]", phone_str):
            raise ValueError("Phone can only contain digits, spaces, or hyphens.")
        
        # Strip everything except numbers
        digits = re.sub(r"\D", "", phone_str)
        if len(digits) != 10:
            raise ValueError("Phone number must be exactly 10 digits.")
        
        # Return formatted string using slicing
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"

    @staticmethod
    def validate_email(email):
        """
        Verifies basic email structure. Allows empty strings if no email
        is provided, otherwise requires '@' and '.'.
        """
        if not email:
            return ""
        if "@" not in email or "." not in email:
            raise ValueError("Invalid email format (must contain @ and .)")
        return email

    @staticmethod
    def validate_zip(zip_code):
        """
        Ensures the zip code string consists of exactly 5 digits.
        """
        digits = re.sub(r"\D", "", zip_code)
        if len(digits) != 5:
            raise ValueError("Zip code must be exactly 5 digits.")
        return digits


class Contact:
    """
    A simple Data Transfer Object (DTO) to represent a single contact.
    This makes it easy to pass contact data around as a single object.
    """

    def __init__(self, name, phone, email, street, city, state, zip_code):
        self.name = name
        self.phone = phone
        self.email = email
        self.street = street
        self.city = city
        self.state = state
        self.zip_code = zip_code

    def to_dict(self):
        """Used for converting the object into a JSON-serializable format."""
        return self.__dict__


class AddressBook:
    """
    The main engine of the application. Handles file I/O, 
    searching, and internal list management.
    """

    def __init__(self, filename="Address Book"):
        # Determine the directory where the script lives to save the file nearby
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.filepath = os.path.join(self.script_dir, filename)
        self.contacts = []
        self.load_from_file()

    def save_to_file(self):
        """Alphabetizes the list and writes it to the JSON file."""
        # Sort using a lambda function to compare lowercase names
        self.contacts.sort(key=lambda c: c.name.lower())
        data = [c.to_dict() for c in self.contacts]
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_from_file(self):
        """Loads data from the JSON file and converts dictionaries back to objects."""
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Reconstruct Contact objects from raw JSON dictionary items
                self.contacts = [Contact(**item) for item in data]
        except (json.JSONDecodeError, IOError, TypeError):
            print("\n[Error] File format error. Please delete the file to reset.")

    def add_contact(self, **data):
        """Appends a new contact and triggers a file save."""
        self.contacts.append(Contact(**data))
        self.save_to_file()
        print(f"\nSuccess: '{data['name']}' has been added.")

    def search_directory(self, query):
        """
        Universal search: Checks if the query string exists in 
        any of the contact's attribute values.
        """
        query = query.lower()
        results = [c for c in self.contacts if any(
            query in str(val).lower() for val in c.to_dict().values()
        )]
        
        if not results:
            print(f"\nNo results for '{query}'.")
        else:
            self._print_table(results)

    def delete_contact(self, name):
        """Searches for a contact by name and deletes them after confirmation."""
        # 'next' finds the first match or returns None
        target = next((c for c in self.contacts 
                       if c.name.lower() == name.lower()), None)
        
        if not target:
            print(f"\nContact '{name}' not found.")
            return

        confirm = input(f"Are you sure you want to delete '{target.name}'? (y/n): ")
        if confirm.lower() == 'y':
            self.contacts.remove(target)
            self.save_to_file()
            print(f"Contact '{target.name}' has been deleted.")
        else:
            print("Deletion canceled.")

    def show_all(self):
        """Displays the entire address book."""
        if not self.contacts:
            print("\nAddress book is empty.")
            return
        self._print_table(self.contacts)

    def _print_table(self, contact_list):
        """Internal helper to print contacts in a formatted text table."""
        header = f"{'Name':<18} | {'Phone':<14} | {'Email':<20} | Address"
        print(f"\n{header}\n{'-' * 95}")
        for c in contact_list:
            addr = f"{c.street}, {c.city}, {c.state} {c.zip_code}"
            print(f"{c.name:<18} | {c.phone:<14} | {c.email:<20} | {addr}")


def get_validated_input(prompt, validation_func):
    """
    A helper function that loops until the user provides 
    input that passes the provided validation function.
    """
    while True:
        user_input = input(prompt)
        try:
            return validation_func(user_input)
        except ValueError as e:
            print(f"  --> [Invalid Input] {e} Please try again.")


def main():
    """Main execution loop for the Command Line Interface."""
    book = AddressBook()
    
    while True:
        print("\n--- ADDRESS BOOK MENU ---")
        print("1. View All")
        print("2. Add Contact")
        print("3. Search Directory")
        print("4. Delete Contact")
        print("5. Exit")
        
        choice = input("\nSelect (1-5): ").strip()
        
        if choice == "1":
            book.show_all()
            
        elif choice == "2":
            print("\nNew Contact Details (Validation active):")
            # Use the 'sticky' validation helper for critical fields
            name = get_validated_input("Name: ", Validator.validate_name)
            phone = get_validated_input("Phone (10 digits): ", Validator.format_phone)
            email = get_validated_input("Email: ", Validator.validate_email)
            
            # Non-critical fields (simple strings)
            street = input("Street: ")
            city = input("City: ")
            state = input("State: ")
            
            zip_code = get_validated_input("Zip (5 digits): ", Validator.validate_zip)

            book.add_contact(
                name=name, phone=phone, email=email, 
                street=street, city=city, state=state, zip_code=zip_code
            )
            
        elif choice == "3":
            query = input("Enter search term (Name/City/Zip/etc): ")
            book.search_directory(query)

        elif choice == "4":
            name = input("Name to delete: ")
            book.delete_contact(name)
            
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid selection. Choose a number between 1 and 5.")


if __name__ == "__main__":
    # Wrap the entire program to catch Ctrl+C (KeyboardInterrupt)
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[System] Program stopped by user. Closing safely...")
