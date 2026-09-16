# Реестр исходных материалов

Сквозной список всех исходных материалов исследования. Сами файлы хранятся **только в архивах
вне git** (`archive/<исследование>/NN-*.zip`); здесь — их номера и привязка к шагам, чтобы ссылки
из `RESEARCH.md` были однозначны.

Типы: `hci` — извлечённый `btsnoop_hci`; `screen` — скриншот; `photo` — фото телефона/помпы.
SHA-256 считается по исходному файлу-артефакту (тому, что внутри архива) как независимый маркер
целостности; проверка — извлечь файл и сверить `sha256sum`.

| № | Тип | Описание | Файл в архиве | SHA-256 | Шаг | Архив |
|---|---|---|---|---|---|---|
| 1 | hci | btsnoop-захват подключения помпы (сессия 16:21–16:25 16.09.2026) | `btsnoop_hci_260916_162139.log` | `18fa271a6e2422b06fdd1108c813e1d0dd3d292390037b66e60829314d4c400d` | 001 | `etap-A-transport-gatt/001-hci.zip` |
| 2 | screen | Экран «Устройства» после подключения (серийный номер замаскирован) | `001_screen_devices_redacted.jpg` | `fb8645114872b7e5c47b2d0985f0b8e65933dc82efd122241bc1723bcaa923f6` | 001 | `etap-A-transport-gatt/001-screens.zip` |
| 3 | screen (комплект) | Скриншоты лицензионного соглашения Erwin Blueberry, Части 1–21 (33 кадра, 16:15–16:17 16.09.2026); провенанс к `user_agreement.md` | `SHA256SUMS.txt` (+ 33 × `eula_NN.jpg`) | `8346f2ae1d27d9b5ab19053339e11fec663ca081122f5fc30768e2b3b8a32916` (манифест; SHA-256 каждого кадра — внутри `SHA256SUMS.txt`) | 002 | `provenance-user-agreement/002-eula-screens.zip` |
| 4 | hci | btsnoop-захват: сессия 16:22 и переподключение 16:52 (Этап A подтверждение + Этап B авторизация) | `btsnoop_hci_260916_162139.log` | `23080b81d563801858caa7142d0cee7092709fcfb7adee610c5191d53dc36a6a` | 003 | `etap-B-avtorizaciya/003-hci.zip` |
| 5 | screen (комплект) | Скриншоты переподключения: «Опасная зона», список устройств, запрос пароля (PIN замаскирован), статус (серийник замаскирован) — 4 кадра | `SHA256SUMS.txt` (+ 4 × `NN_*.jpg`) | `05332ab7ee373c168d70ea906bfd6aa1961d05113a46da8ea49f9f1e00577883` (манифест) | 003 | `etap-B-avtorizaciya/003-screens.zip` |
| 6 | photo | Фото экрана помпы, меню «СОСТОЯНИЕ» (строки S/N и B/P замаскированы) | `pump_status_redacted.jpg` | `cdff52afea63e945beeea20f7ed1d7980c94d330d0c28d1e4788b7171e88fcf0` | 003 | `etap-B-avtorizaciya/003-photos.zip` |
| 7 | screen (комплект) | Скриншоты меню приложения (5 кадров): Главная, История, Настройки болюса, Настройки базала, Вспомогат. функции | `SHA256SUMS.txt` (+ 5 × `NN_*.jpg`) | `6fae003ed2907a8950b3bda3892ec169a2fe3de8405d24eb215d58e560630e91` (манифест) | 005 | `app-menu-map/005-menu-screens.zip` |
| 8 | hci | btsnoop-захват G1 (статус в 18:01–18:02) | `btsnoop_hci_260916_162139_g1.log` | `8ced4e96143970f8502ef7e120d6cf45bc833f9c4b3419696ada523610183f38` | 006 | `etap-D-g1-status/006-hci.zip` |
| 9 | screen (комплект) | Скриншоты статуса 18:01: Главная (IOB 1,87), Устройства (батарея 1,36В/46%, серийник замаскирован) | `SHA256SUMS.txt` (+ 2 × jpg) | `f6a93ccc78af0925b5739fb33b836e0980b552fcaa0f6a5f3b513466ebf485e7` (манифест) | 006 | `etap-D-g1-status/006-screens.zip` |
| 10 | hci | btsnoop-захват G3: смена макс. болюса 12,0→12,3 (a3/00 off26; команда a1/32) | `btsnoop_hci_260916_162139_g3.log` | `368eede7629c0e25a51ca0dac572a11c3a4913895fa981b2b6614d0e1690b705` | 009 | `etap-E-zapis-nastroek/009-hci.zip` |
| 11 | hci | btsnoop-захват: смена макс. базала 8,0→7,7 (a3/00 off24; команда a1/32) | `btsnoop_hci_260916_162139_maxbasal.log` | `d6d392cc558a5a708c7108ba5cc0fa91ba280004467666f5bd07feafa9037d2b` | 010 | `etap-E-zapis-nastroek/010-hci.zip` |
| 12 | hci | btsnoop-захват серии настроек 20:16–20:18 (команды a1/32, a1/34) | `btsnoop_hci_260916_162139_settings.log` | `18f191c58f01599128265c901608716d4763fd55556ea0ad7b934be277a0210a` | 011 | `etap-E-nastroiki-boljus/011-hci.zip` |
| 13 | screen (комплект) | Скриншоты «Настройки болюса» в ходе серии (4 кадра): расш. болюс/звук ВКЛ, шаг звука 5,0→0,1, скорость «Низкая» | `SHA256SUMS.txt` (+ 4 × jpg) | `c85834e80b042531fb81e52d8e0b657dc72d5f04a8dd2e4d5caddf1c935a158d` (манифест) | 011 | `etap-E-nastroiki-boljus/011-screens.zip` |
| 14 | hci | btsnoop-захват: напоминание о ГК (a1/32 байт[6]) и предустановки болюса (a1/11), 22:42–22:43 | `btsnoop_hci_gk_presety.log` | `40665175df9ca7fdc348d05f4e751ceee2b8711f6e26c1e02f6b36abd55a4c0f` | 012 | `etap-E-gk-presety/012-hci.zip` |
| 15 | screen (комплект) | Скриншоты «Предустановки болюса» (2 кадра: до/после правки) | `SHA256SUMS.txt` (+ 2 × jpg) | `f373cdeb5efa97ab3e7615fd03a96a64f2522d84c83efaba70a2e69465498de4` (манифест) | 012 | `etap-E-gk-presety/012-screens.zip` |
