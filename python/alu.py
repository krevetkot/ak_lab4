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

    def plus(self, right, left):
        """Сложение с установкой флагов"""
        result = right + left
        self._update_nz(result)

        max_uint32 = 0xFFFFFFFF
        max_int32 = 0x7FFFFFFF
        min_int32 = -0x80000000

        self.c = (right + left) > max_uint32
        self.v = (right > 0 and left > 0 and result > max_int32) or \
                 (right < 0 and left < 0 and result < min_int32)
        return result

    def minus(self, right, left):
        """Вычитание с установкой флагов"""
        result = right - left
        self._update_nz(result)

        max_uint32 = 0xFFFFFFFF
        self.c = right < left  # Перенос при вычитании (если right < left)
        
        # Переполнение для вычитания
        self.v = (right >= 0 and left < 0 and result < 0) or \
                 (right < 0 and left >= 0 and result > 0)
        return result

    def multiply(self, right, left):
        """Умножение с установкой флагов"""
        result = right * left
        self._update_nz(result)

        # Проверка переполнения для умножения
        if right != 0 and (result // right) != left:
            self.v = 1
        else:
            self.v = 0
            
        self.c = 0  # Для умножения перенос обычно не используется
        return result

    def divide(self, right, left):
        """Деление с установкой флагов"""
        if left == 0:
            raise ZeroDivisionError("Division by zero")
            
        result = left // right
        self._update_nz(result)
        self.v = 0  # Деление не вызывает переполнения
        self.c = 0  # Нет переноса
        return result

    def modulo(self, right, left):
        """Остаток от деления с установкой флагов"""
        if left == 0:
            raise ZeroDivisionError("Modulo by zero")
            
        result = left % right
        self._update_nz(result)
        self.v = 0
        self.c = 0
        return result

    def logical_and(self, right, left):
        """Логическое AND с установкой флагов"""
        result = left & right
        self._update_nz(result)
        self.v = 0
        self.c = 0
        return result

    def logical_or(self, right, left):
        """Логическое OR с установкой флагов"""
        result = left | right
        self._update_nz(result)
        self.v = 0
        self.c = 0
        return result

    def logical_not(self, right):
        """Логическое NOT с установкой флагов"""
        result = ~right
        self._update_nz(result)
        self.v = 0
        self.c = 0
        return result