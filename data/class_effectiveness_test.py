from data.classes import classes


def calculate_class_scores(classes):
    class_scores = {}
    for class_name, attributes in classes.items():
        vulnerabilities = attributes.get("vulnerabilities", [])
        resistances = attributes.get("resistances", [])
        synergies = attributes.get("synergies", [])

        score = -1 * len(vulnerabilities) + 0.9

        class_scores[class_name] = round(score, 2)

    return class_scores


class_scores = calculate_class_scores(classes)

for class_name, score in class_scores.items():
    print(f"{class_name}: {score}")
