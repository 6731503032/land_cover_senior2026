"""Class names and the mapping between datasets. Edit here, nowhere else."""

# Our project classes (placeholder list: change to match your final decision)
PROJECT_CLASSES = ["Bareland", "Rangeland", "Road", "Tree", "Water", "Agriculture", "Building"]

# OpenEarthMap's 8 classes, in order (verify against the dataset page)
OEM_CLASSES = ["Bareland", "Rangeland", "Developed space", "Road",
               "Tree", "Water", "Agriculture", "Building"]

# OEM id -> project id. None = ignore that pixel when training.
# "Developed space" has no project class yet: decide in docs/decisions.md.
OEM_TO_PROJECT = {
    0: 0,     # Bareland -> Bareland
    1: 1,     # Rangeland -> Rangeland
    2: None,  # Developed space -> undecided
    3: 2,     # Road -> Road
    4: 3,     # Tree -> Tree
    5: 4,     # Water -> Water
    6: 5,     # Agriculture -> Agriculture
    7: 6,     # Building -> Building
}

# IRSAMap: fill in after reading its class table
IRSA_TO_PROJECT = {}

IGNORE_INDEX = 255
