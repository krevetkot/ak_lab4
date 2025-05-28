#!/usr/bin/python3


class ALU:
    def __init__(self):
        self.reset_flags()
        self.result = 0

    def get_result(self):
        return self.result

    def reset_flags(self):
        self.n = 0
        self.z = 1
        self.v = 0
        self.c = 0

    def _update_nz(self, result):
        """Обновление флагов N и Z"""
        self.result = result
        self.n = 1 if result < 0 else 0
        self.z = 1 if result == 0 else 0

    def do_ALU(self, right, left, sel):  # noqa: C901, N802
        if sel == 0:
            self.plus_zero(left)
        elif sel == 1:
            self.plus(right, left)
        elif sel == 2:
            self.minus(right, left)
        elif sel == 3:
            self.multiply(right, left)
        elif sel == 4:
            self.divide(right, left)
        elif sel == 5:
            self.modulo(right, left)
        elif sel == 6:
            self.logical_and(right, left)
        elif sel == 7:
            self.logical_or(right, left)
        elif sel == 8:
            self.logical_not(right)
        elif sel == 9:
            self.equal(right, left)
        elif sel == 10:
            self.less(right, left)
        elif sel == 11:
            self.greater(right, left)

    def plus_zero(self, left):
        self.result = left

    def plus(self, right, left):
        """Сложение с установкой флагов"""
        result = right + left
        self._update_nz(result)

        max_uint32 = 0xFFFFFFFF
        max_int32 = 0x7FFFFFFF
        min_int32 = -0x80000000

        self.c = (right + left) > max_uint32
        self.v = (right > 0 and left > 0 and result > max_int32) or (right < 0 and left < 0 and result < min_int32)

    def minus(self, right, left):
        """Вычитание с установкой флагов"""
        result = left - right
        self._update_nz(result)
        self.c = right < left  # Перенос при вычитании (если right < left)

        # Переполнение для вычитания
        self.v = (right >= 0 and left < 0 and result < 0) or (right < 0 and left >= 0 and result > 0)

    def multiply(self, right, left):
        """Умножение с установкой флагов"""
        result = left * right
        self._update_nz(result)

        # Проверка переполнения для умножения
        if right != 0 and (result // right) != left:
            self.v = 1
        else:
            self.v = 0

        self.c = 0  # Для умножения перенос обычно не используется

    def divide(self, right, left):
        """Деление с установкой флагов"""
        if left == 0:
            raise ZeroDivisionError("Division by zero")  # noqa: TRY003

        result = left // right
        self._update_nz(result)
        self.v = 0  # Деление не вызывает переполнения
        self.c = 0  # Нет переноса

    def modulo(self, right, left):
        """Остаток от деления с установкой флагов"""
        if left == 0:
            raise ZeroDivisionError("Modulo by zero")  # noqa: TRY003

        result = left % right
        self._update_nz(result)
        self.v = 0
        self.c = 0

    def logical_and(self, right, left):
        """Логическое AND с установкой флагов"""
        result = left & right
        self._update_nz(result)
        self.v = 0
        self.c = 0

    def logical_or(self, right, left):
        """Логическое OR с установкой флагов"""
        result = left | right
        self._update_nz(result)
        self.v = 0
        self.c = 0

    def logical_not(self, right):
        """Логическое NOT с установкой флагов"""
        result = ~right
        self._update_nz(result)
        self.v = 0
        self.c = 0

    def equal(self, right, left):
        """Проверка на равенство с установкой флагов"""
        if right == left:
            result = -1
        else:
            result = 0
        self._update_nz(result)
        self.v = 0
        self.c = 0

    def less(self, right, left):
        """Меньше с установкой флагов"""
        if left < right:
            result = -1
        else:
            result = 0
        self._update_nz(result)
        self.v = 0
        self.c = 0

    def greater(self, right, left):
        """Больше с установкой флагов"""
        if left > right:
            result = -1
        else:
            result = 0
        self._update_nz(result)
        self.v = 0
        self.c = 0
