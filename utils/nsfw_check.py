from nudenet import NudeDetector


def contains_pornographic_content(image_path, threshold=0.6):
    """
    Проверяет, содержит ли изображение порнографический контент.

    :param image_path: Путь к изображению.
    :param threshold: Уровень уверенности, начиная с которого объект считается порнографическим.
    :return: True, если обнаружен порнографический контент, иначе False.
    """
    # Создание экземпляра классификатора
    detector = NudeDetector()

    # Проверка изображения
    results = detector.detect(image_path)

    # Классы, которые считаются порнографическими
    pornographic_classes = {
        "FEMALE_BREAST_EXPOSED",
        "FEMALE_GENITALIA_EXPOSED",
        "BUTTOCKS_EXPOSED",
        "ANUS_EXPOSED",
        "MALE_GENITALIA_EXPOSED"
    }

    # Проверка каждого обнаруженного объекта
    for result in results:
        if result['class'] in pornographic_classes and result['score'] >= threshold:
            return True  # Найден порнографический контент

    return False  # Ничего не найдено


# Пример использования
image_path = "test.jpeg"
is_porn = contains_pornographic_content(image_path)

print(f"Порнографическое содержимое: {'Да' if is_porn else 'Нет'}")
