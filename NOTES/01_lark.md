# Полное руководство по Lark: создание своего языка программирования

## Содержание
1. [Введение в Lark](#введение-в-lark)
2. [Основные концепции](#основные-концепции)
3. [Установка и первые шаги](#установка-и-первые-шаги)
4. [Грамматика EBNF](#грамматика-ebnf)
5. [Типы парсеров в Lark](#типы-парсеров-в-lark)
6. [Трансформеры и посетители](#трансформеры-и-посетители)
7. [Примеры использования](#примеры-использования)
8. [Продвинутые техники](#продвинутые-техники)
9. [Отладка грамматик](#отладка-грамматик)
10. [Лучшие практики](#лучшие-практики)

## Введение в Lark

Lark - это библиотека для синтаксического анализа в Python, которая позволяет создавать парсеры на основе контекстно-свободных грамматик. Она названа в честь птицы жаворонок ("lark" по-английски), что символизирует свободу и легкость, которую предоставляет библиотека при написании парсеров.

Ключевые преимущества Lark:
- Простой и понятный синтаксис определения грамматик
- Высокая производительность
- Поддержка как восходящего (Earley), так и нисходящего (LALR) парсинга
- Обработка неоднозначных грамматик
- Встроенная система построения абстрактных синтаксических деревьев (AST)
- Автоматическая обработка пробелов и комментариев

## Основные концепции

Перед тем как погрузиться в детали, давайте разберем основные концепции:

### Терминалы и нетерминалы

- **Терминалы** (токены) - элементарные единицы языка, которые нельзя разделить дальше. Например, ключевые слова, числа, строки.
- **Нетерминалы** - правила грамматики, которые состоят из терминалов и других нетерминалов.

### Лексер и парсер

- **Лексер** (токенизатор) - преобразует входной текст в последовательность токенов.
- **Парсер** - анализирует последовательность токенов и строит синтаксическое дерево согласно правилам грамматики.

### Синтаксическое дерево

- **Конкретное синтаксическое дерево** (Parse Tree) - точное представление разбора входного текста согласно грамматике.
- **Абстрактное синтаксическое дерево** (AST) - упрощенное представление, фокусирующееся на семантической структуре.

## Установка и первые шаги

### Установка

```bash
pip install lark
```

### Простейший пример

Вот пример простого калькулятора:

```python
from lark import Lark

# Определение грамматики
calc_grammar = """
    ?start: sum

    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub

    ?product: atom
        | product "*" atom  -> mul
        | product "/" atom  -> div

    ?atom: NUMBER           -> number
        | "-" atom          -> neg
        | "(" sum ")"

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

# Создание парсера
parser = Lark(calc_grammar, parser='lalr', transformer=CalcTransformer())

# Использование парсера
result = parser.parse("2 + 3 * (4 - 2)")
print(result)  # Выведет 8
```

### Выполнение вычислений

Для выполнения операций нам нужен трансформер:

```python
from lark import Transformer

class CalcTransformer(Transformer):
    def add(self, args):
        return args[0] + args[1]
    
    def sub(self, args):
        return args[0] - args[1]
    
    def mul(self, args):
        return args[0] * args[1]
    
    def div(self, args):
        return args[0] / args[1]
    
    def neg(self, args):
        return -args[0]
    
    def number(self, args):
        return float(args[0])
```

## Грамматика EBNF

Lark использует расширенную форму Бэкуса-Наура (EBNF) для описания грамматик.

### Основные элементы синтаксиса

- `rule: expression` - определение правила
- `?rule: expression` - инлайн-правило (не создает узел в дереве)
- `"string"` - литерал строки
- `/regexp/` - регулярное выражение
- `rule1 rule2` - последовательность
- `rule1 | rule2` - альтернатива
- `[rule]` - опциональное правило (0 или 1)
- `{rule}` - повторение (0 или более)
- `{rule}+` - повторение (1 или более)
- `(rule1 rule2)` - группировка
- `-> name` - именование правила для трансформации

### Импорт и директивы

- `%import common.NUMBER` - импорт стандартных определений
- `%ignore WS` - игнорирование пробельных символов
- `%declare` - объявление токена без его определения

## Типы парсеров в Lark

Lark поддерживает несколько типов парсеров:

### LALR(1)

```python
parser = Lark(grammar, parser='lalr')
```

- Быстрый и эффективный
- Ограничен контекстно-свободными грамматиками
- Не поддерживает левую рекурсию
- Используется по умолчанию

### Earley

```python
parser = Lark(grammar, parser='earley')
```

- Поддерживает все контекстно-свободные грамматики
- Поддерживает левую рекурсию
- Медленнее, чем LALR
- Хорошо подходит для неоднозначных грамматик

### CYK

```python
parser = Lark(grammar, parser='cyk')
```

- Основан на алгоритме Кока-Янгера-Касами
- Работает только с грамматиками в нормальной форме Хомского
- Используется редко, в основном для теоретических целей

## Трансформеры и посетители

Lark предоставляет два основных способа обработки синтаксических деревьев:

### Трансформеры (Transformers)

Трансформеры преобразуют дерево снизу вверх, заменяя узлы результатами вызовов методов:

```python
from lark import Transformer, v_args

@v_args(inline=True)  # Передаёт аргументы напрямую, а не как список
class MyTransformer(Transformer):
    def integer(self, value):
        return int(value)
    
    def add(self, left, right):
        return left + right
    
    def sub(self, left, right):
        return left - right
```

### Посетители (Visitors)

Посетители обходят дерево, не изменяя его структуру:

```python
from lark.visitors import Visitor

class CountNodes(Visitor):
    def __init__(self):
        self.count = 0
    
    def __default__(self, tree):
        self.count += 1
```

### Интерпретеры (Interpreters)

Комбинация трансформера и посетителя:

```python
from lark.visitors import Interpreter

class MyInterpreter(Interpreter):
    def integer(self, tree):
        return int(tree.children[0])
    
    def add(self, tree):
        left, right = tree.children
        return self.visit(left) + self.visit(right)
```

## Примеры использования

### 1. Простой язык программирования

```python
from lark import Lark, Transformer

# Определение простого языка с переменными и выражениями
mini_lang_grammar = r"""
    ?program: statement+

    ?statement: assignment ";"
            | print_stmt ";"

    assignment: NAME "=" expression

    print_stmt: "print" expression

    ?expression: sum

    ?sum: product
        | sum "+" product    -> add
        | sum "-" product    -> sub

    ?product: atom
        | product "*" atom   -> mul
        | product "/" atom   -> div

    ?atom: NUMBER            -> number
        | NAME               -> variable
        | "-" atom           -> neg
        | "(" expression ")"

    NAME: /[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

# Интерпретатор для языка
class MiniLangInterpreter(Transformer):
    def __init__(self):
        super().__init__()
        self.variables = {}
    
    def assignment(self, args):
        name, value = args
        self.variables[name] = value
        return value
    
    def print_stmt(self, args):
        value = args[0]
        print(value)
        return value
    
    def add(self, args):
        left, right = args
        return left + right
    
    def sub(self, args):
        left, right = args
        return left - right
    
    def mul(self, args):
        left, right = args
        return left * right
    
    def div(self, args):
        left, right = args
        return left / right
    
    def neg(self, args):
        return -args[0]
    
    def number(self, args):
        return float(args[0])
    
    def variable(self, args):
        name = args[0]
        if name not in self.variables:
            raise NameError(f"Variable '{name}' not defined")
        return self.variables[name]

# Создание парсера
parser = Lark(mini_lang_grammar, parser='lalr', transformer=MiniLangInterpreter())

# Пример программы
program = """
    x = 10;
    y = 20;
    z = x + y * 2;
    print z;
"""

# Выполнение программы
parser.parse(program)  # Выведет 50.0
```

### 2. Парсер JSON

```python
from lark import Lark, Transformer
import json

json_grammar = r"""
    ?start: value

    ?value: object
         | array
         | string
         | SIGNED_NUMBER      -> number
         | "true"             -> true
         | "false"            -> false
         | "null"             -> null

    array: "[" [value ("," value)*] "]"
    object: "{" [pair ("," pair)*] "}"
    pair: string ":" value

    string: ESCAPED_STRING

    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS
"""

class JsonTransformer(Transformer):
    def string(self, s):
        return s[0][1:-1]  # Убираем кавычки
    
    def number(self, n):
        return float(n[0])
    
    def true(self, _):
        return True
    
    def false(self, _):
        return False
    
    def null(self, _):
        return None
    
    def array(self, items):
        return list(items)
    
    def pair(self, kv):
        k, v = kv
        return k, v
    
    def object(self, pairs):
        return dict(pairs)

# Создание парсера
json_parser = Lark(json_grammar, parser='lalr', transformer=JsonTransformer())

# Пример JSON
json_text = '{"name": "John", "age": 30, "hobbies": ["reading", "music"]}'

# Парсинг JSON
result = json_parser.parse(json_text)
print(result)  # Выведет объект Python
```

## Продвинутые техники

### Контекстно-зависимый анализ

Для некоторых языков требуется контекстно-зависимый анализ. Хотя Lark не поддерживает это напрямую, можно использовать пост-обработку:

```python
from lark import Lark, Visitor

# Проверка объявления переменных перед использованием
class VariableResolver(Visitor):
    def __init__(self):
        self.declared_vars = set()
        self.errors = []
    
    def visit_assignment(self, node):
        var_name = node.children[0].value
        self.declared_vars.add(var_name)
    
    def visit_variable(self, node):
        var_name = node.children[0].value
        if var_name not in self.declared_vars:
            self.errors.append(f"Error: Variable '{var_name}' used before declaration")
```

### Контроль ошибок

Lark предоставляет возможности для обработки синтаксических ошибок:

```python
from lark import Lark, UnexpectedInput

parser = Lark(grammar, parser='lalr')

try:
    tree = parser.parse(text)
except UnexpectedInput as e:
    print(f"Ошибка: {e}")
    print(f"Строка: {e.line}, Позиция: {e.column}")
    print(e.get_context(text, 2))  # Показать контекст ошибки
```

### Инкрементальный парсинг

Для парсинга больших файлов или потоков данных:

```python
from lark import Lark

parser = Lark(grammar, parser='lalr')
parser_inst = parser.parse_interactive()

for line in stream:
    parser_inst.feed(line)
    # ... обработка промежуточных результатов
```

## Отладка грамматик

### Визуализация деревьев

Lark позволяет визуализировать синтаксические деревья:

```python
from lark import Lark
from lark.tree import pydot__tree_to_png

parser = Lark(grammar)
tree = parser.parse(text)

# Сохранить изображение дерева
pydot__tree_to_png(tree, "parse_tree.png")
```

### Трассировка

Для отладки можно включить режим трассировки:

```python
parser = Lark(grammar, parser='lalr', debug=True)
```

### Инструменты профилирования

Для оптимизации производительности используйте стандартные инструменты профилирования Python:

```python
import cProfile

cProfile.run('parser.parse(large_text)')
```

## Лучшие практики

1. **Начинайте с малого** - разрабатывайте грамматику постепенно, начиная с простых конструкций.

2. **Тестируйте каждое изменение** - создавайте тесты для различных сценариев ввода.

3. **Используйте именованные правила** - они делают грамматику более читаемой и упрощают отладку:
   ```
   expr: term "+" term -> add
        | term "-" term -> subtract
   ```

4. **Выделяйте общие конструкции** - это упрощает поддержку и расширение грамматики.

5. **Разделяйте лексические и синтаксические правила** - это улучшает производительность и понятность.

6. **Используйте стандартные токены** - Lark предоставляет много готовых определений:
   ```
   %import common.NUMBER
   %import common.WS
   %import common.CNAME
   ```

7. **Обрабатывайте ошибки** - хорошие сообщения об ошибках значительно упрощают отладку.

8. **Документируйте грамматику** - комментарии помогают понять сложные конструкции.

## Кейсы использования Lark

Lark отлично подходит для следующих задач:

1. **Создание предметно-ориентированных языков (DSL)** - настраиваемые языки для специфических доменов.

2. **Парсинг конфигурационных файлов** - создание мощных и гибких форматов конфигурации.

3. **Анализ кода** - статический анализ, рефакторинг, форматирование.

4. **Обработка естественного языка** - парсинг предложений и текстов.

5. **Компиляторы и интерпретаторы** - создание полноценных языков программирования.

6. **Конвертеры форматов** - преобразование между различными представлениями данных.

## Заключение

Lark - мощный и гибкий инструмент для создания парсеров и обработки языков. С его помощью можно реализовать широкий спектр задач от простых DSL до полноценных языков программирования. Ключ к успеху - постепенное развитие грамматики, тщательное тестирование и понимание различных подходов к парсингу. 