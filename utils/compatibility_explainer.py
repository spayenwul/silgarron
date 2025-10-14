from services.compatibility_service import CompatibilityScore

def explain_compatibility(score: CompatibilityScore, title: str = "Compatibility Analysis") -> str:
    """
    Создает человекочитаемое объяснение результата совместимости.
    Полезно для отладки и понимания, почему система приняла решение.
    """
    lines = [
        f"=== {title} ===",
        f"  - Итоговый счет: {score.raw_score:.2f}",
        f"  - Уровень: {score.level.name}",
        f"  - Совместимость: {'Да' if score.is_compatible else 'Нет'}",
    ]
    
    if score.blocking_factors:
        lines.append("  - ❌ Блокирующие факторы:")
        for factor in score.blocking_factors:
            lines.append(f"    - {factor}")
    
    if score.breakdown:
        lines.append("  - 📊 Детализация расчета:")
        for component, value in score.breakdown.items():
            lines.append(f"    - {component}: {value:.2f}")
    
    lines.append("=" * (len(title) + 6))
    return "\n".join(lines)

# Пример использования, если запустить файл напрямую
if __name__ == "__main__":
    from services.compatibility_service import CompatibilityLevel

    print("--- Пример объяснения для СОВМЕСТИМОГО результата ---")
    good_score = CompatibilityScore(
        raw_score=1.8,
        level=CompatibilityLevel.EXCELLENT,
        breakdown={"base_score": 1.2, "synergy_bonus": 1.5},
        blocking_factors=[]
    )
    print(explain_compatibility(good_score, "Kith vs Pulsating Plains"))

    print("\n--- Пример объяснения для НЕСОВМЕСТИМОГО результата ---")
    bad_score = CompatibilityScore(
        raw_score=0.0,
        level=CompatibilityLevel.INCOMPATIBLE,
        breakdown={},
        blocking_factors=["Sharp transition rule: Жар и влажность несовместимы"]
    )
    print(explain_compatibility(bad_score, "Biolume Forest vs Geyser Fields"))