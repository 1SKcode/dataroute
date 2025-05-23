# Условные конструкции в DataRoute

## Введение

Условные конструкции в DataRoute позволяют создавать динамические маршруты обработки данных на основе значений полей и переменных. С помощью условных конструкций можно выполнять разные действия в зависимости от условий, что значительно расширяет возможности DSL.

## Синтаксис

### Простое условие IF/ELSE

```
[поле] -> |IF(условие): действие1 ELSE: действие2| -> [результат](тип)
```

### Расширенное условие с ELIF

```
[поле] -> |IF(условие1): действие1 ELIF(условие2): действие2 ELSE: действие3| -> [результат](тип)
```

## Примеры использования

### Простая проверка значений

```
# Проверка числового значения
[pointA] -> |IF($this == 100): *func1 ELSE: *func2| -> [pointB](str)

# Проверка строкового значения
[status] -> |IF($this == "active"): *process_active ELSE: *process_inactive| -> [normStatus](str)
```

### Проверка на None

```
[pointC] -> |IF($this == None): SKIP("Пропущено, т.к. значение None") ELSE: *process_value| -> [pointD](int)
```

### Использование глобальных переменных в условиях

```
# Глобальная переменная
$myVar2 = 42

# Использование в условии
[pointE] -> |IF($this > $myVar2): *func_large ELSE: *func_small| -> [pointF](float)
```

### Несколько условий с ELIF

```
[status] -> |IF($this == "active"): *process_active ELIF($this == "pending"): *process_pending ELSE: ROLLBACK("Неизвестный статус")| -> [normStatus](str)
```

### Проверка вхождения в множество (оператор IN)

```
[category] -> |IF($this IN $$categories.allowed): *process_category ELSE: SKIP("Категория не разрешена")| -> [normCategory](str)
```

### Использование локальных переменных

```
# Создание локальной переменной
[age] -> |*normalize_age| -> [$normalized_age](int)

# Использование локальной переменной в условии
[height] -> |IF($normalized_age > 18): *adult_height_check ELSE: *child_height_check| -> [heightValid](bool)
```

## События в условиях

В ветвях условий можно использовать следующие события:

- **SKIP(сообщение)** - пропустить запись с указанным сообщением
- **ROLLBACK(сообщение)** - отменить всю обработку с указанным сообщением
- **NOTIFY(сообщение)** - отправить уведомление

Пример:
```
[price] -> |IF($this < 0): ROLLBACK("Цена не может быть отрицательной") ELIF($this == 0): SKIP("Пропущено, т.к. цена равна нулю") ELSE: *process_price| -> [normPrice](float)
```

## Возможные ошибки и их исправление

1. **ELSE без IF**
   - Ошибка: `[test] -> |ELSE: *func2| -> [result](str)`
   - Решение: Используйте конструкцию с IF: `IF(условие): действие1 ELSE: действие2`

2. **IF без скобок**
   - Ошибка: `[test] -> |IF: *func ELSE: *func2| -> [result](str)`
   - Решение: Добавьте скобки с условием: `IF(условие): *func ELSE: *func2`

3. **Пустые скобки в условии**
   - Ошибка: `[test] -> |IF(): *func1 ELSE: *func2| -> [result](str)`
   - Решение: Добавьте условие внутри скобок: `IF($this > 0): *func1 ELSE: *func2`

4. **Отсутствие двоеточия после условия**
   - Ошибка: `[test] -> |IF($this > 10) *func1 ELSE: *func2| -> [result](str)`
   - Решение: Добавьте двоеточие: `IF($this > 10): *func1 ELSE: *func2`

5. **Использование несуществующей переменной**
   - Ошибка: `[test] -> |IF($not_exists > 10): *func1 ELSE: *func2| -> [result](str)`
   - Решение: Используйте определенную переменную или $this: `IF($this > 10): *func1 ELSE: *func2` 