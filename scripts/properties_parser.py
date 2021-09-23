from dataclasses import dataclass

# Parser to read and modify Minecraft server.properties files
@dataclass
class PropertiesParser:
    file_path: str
    data: dict
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = dict()
        with open(file_path, "r") as f:
            for l in f:
                line = l.strip()
                
                # Skip comments
                if line.startswith("#"):
                    continue
                values = line.split("=")
                if len(values) != 2:
                    continue

                prop, val = values
                self.data[prop] = val
    
    # Gets the value of property
    def get(self, prop: str):
        return self.data.get(prop)
    
    # Sets property 'prop' to 'val'
    def set(self, prop: str, val: str):
        self.data[prop] = val

    # Saves the data to the original file
    # Comments are not saved since they're not important
    def save(self):
        with open(self.file_path, "w") as f:
            for prop, val in self.data.items():
                f.write(f"{prop}={val}\n")
