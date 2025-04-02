# Директория для хранения ключей ЭЦП

## Требования к ключам

1. **Приватный ключ (private_key.pem)**:
   - Формат: PEM
   - Алгоритм: RSA 2048 или выше
   - Без пароля (для автоматизации)
   - Права доступа: 600 (только владелец)

2. **Публичный ключ (public_key.pem)**:
   - Формат: PEM
   - Права доступа: 644 (чтение для всех)

## Генерация ключей

```bash
# Генерация приватного ключа
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048

# Создание публичного ключа из приватного
openssl rsa -pubout -in private_key.pem -out public_key.pem

# Установка прав доступа
chmod 600 private_key.pem
chmod 644 public_key.pem
