import json

class VCDParser:
    def __init__(self):
        self.timescale = None
        self.variables = {}
        self.timeline = {}
        self.current_time = '0'  # Initialize current_time
        self.register_changes = {}  # New structure to track changes per register name
        self.previous_changes = {}  # Track changes at the previous time interval

    def parse_line(self, line):
        if not line:  # Check if the line is empty
            return
        if line.startswith('$timescale'):
            parts = line.split()
            if len(parts) > 1:
                self.timescale = parts[1]
            else:
                print("Error: Timescale definition is incomplete.")
        elif line.startswith('$var'):
            parts = line.split()
            if len(parts) >= 5:
                var_id = parts[3]
                var_name = parts[4]
                if var_name.startswith("shadow_"):  # Only include shadow registers
                    self.variables[var_id] = {'type': parts[1], 'size': parts[2], 'name': var_name}
            else:
                print("Error: Variable definition is incomplete.")
        elif line.startswith('#'):  # Handle time change
            self.current_time = line[1:].strip()
            # Move current changes to previous changes
            if self.current_time in self.timeline:
                self.previous_changes = self.timeline[self.current_time].copy()
            else:
                self.previous_changes = {}
        elif line and line[0] in ('0', '1', 'x', 'z'):  # Check if line is not empty before accessing index 0
            time, var_id, value = self.extract_value_change(line)
            if time is not None and var_id is not None and value is not None:
                if var_id in self.variables:  # Only process shadow registers
                    if time not in self.timeline:
                        self.timeline[time] = {}
                    self.timeline[time][var_id] = value
                    self.aggregate_register_changes(time, var_id, value)
            else:
                print("Error: Invalid value change line.")

    def extract_value_change(self, line):
        try:
            if not line:  # Check if the line is empty
                return None, None, None
            if line[0] in ('0', '1', 'x', 'z'):
                value = line[0]
                var_id = line[1:].strip() if len(line) > 1 else None  # Check length before stripping
                time = self.current_time  # Use the current_time
            else:
                print("Error: Invalid value change format.")
                return None, None, None
            return time, var_id, value
        except IndexError as e:
            print(f"Error parsing value change: {e}")
            return None, None, None

    def aggregate_register_changes(self, time, var_id, value):
        var_name = self.variables[var_id]['name'] if var_id in self.variables else var_id
        if var_name not in self.register_changes:
            self.register_changes[var_name] = {}
        if time not in self.register_changes[var_name]:
            self.register_changes[var_name][time] = value
        else:
            # Perform logical OR operation
            current_value = self.register_changes[var_name][time]
            if current_value == '1' or value == '1':
                self.register_changes[var_name][time] = '1'
            elif current_value == '0' and value == '0':
                self.register_changes[var_name][time] = '0'
            else:
                self.register_changes[var_name][time] = 'x'  # Handle unknown states

    def read_vcd(self, file_path):
        with open(file_path, 'r') as file:
            for line in file:
                self.parse_line(line.strip())

    def to_json(self, file_path):
        data = {
            "timescale": self.timescale,
            "variables": self.variables,
            "timeline": self.timeline,
            "register_changes": self.register_changes
        }
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

def main():
    parser = VCDParser()
    parser.read_vcd('/Users/jacobplax/Desktop/Data 597 Research/DATA597/vcds/ACLK.vcd')
    parser.to_json('/Users/jacobplax/Desktop/Data 597 Research/DATA597/ACLK.json')
    print("Aggregated Shadow Register Changes by Time:")
    # Create a new dictionary to store the aggregated changes by time
    aggregated_timeline = {}
    previous_changes = {}
    for var_name, changes in parser.register_changes.items():
        for time, value in changes.items():
            if time not in aggregated_timeline:
                aggregated_timeline[time] = {}
            if var_name not in aggregated_timeline[time]:
                aggregated_timeline[time][var_name] = value
            else:
                # Perform logical OR operation
                current_value = aggregated_timeline[time][var_name]
                if current_value == '1' or value == '1':
                    aggregated_timeline[time][var_name] = '1'
                elif current_value == '0' and value == '0':
                    aggregated_timeline[time][var_name] = '0'
                else:
                    aggregated_timeline[time][var_name] = 'x'  # Handle unknown states

    for time, changes in sorted(aggregated_timeline.items()):
        print(f"At time {time}:")
        for var_name, value in changes.items():
            print(f"  Shadow Register {var_name} changed to {value}")
            if previous_changes:
                print(f"    Caused by changes in previous interval: {previous_changes}")
        previous_changes = changes.copy()

if __name__ == '__main__':
    main()