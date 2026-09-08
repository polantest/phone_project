# iPhone 16e stock checker

Sprawdza co N minut, czy [iPhone 16e na Amazon.fr](https://www.amazon.fr/dp/B0DXQHPY34) jest dostępny,
i wysyła powiadomienie Telegram (+opcjonalnie e-mail), gdy pojawi się przycisk kupna.

## Jak to działa
- `check_stock.py` otwiera stronę produktu w headless Chromium (Playwright) i sprawdza tekst dostępności
  (`#availability`) oraz obecność przycisku `#buy-now-button` / `#add-to-cart-button`.
  **Zwykłe zapytania HTTP (`requests`) nie działają** — Amazon od razu pokazuje ekran
  "kliknij, aby kontynuować zakupy" zamiast strony produktu; prawdziwa przeglądarka to omija.
- GitHub Actions (`.github/workflows/check-stock.yml`) uruchamia skrypt co 5 minut za darmo — nie trzeba
  nic hostować (workflow doinstalowuje Chromium przy każdym uruchomieniu).

## Konfiguracja (jednorazowo)

### 1. Telegram (rekomendowane, w pełni darmowe)
1. W Telegramie napisz do **@BotFather** → `/newbot` → nadaj nazwę → dostaniesz `TELEGRAM_BOT_TOKEN`.
2. Napisz cokolwiek do swojego nowego bota (musi mieć z tobą otwartą konwersację).
3. Wejdź na `https://api.telegram.org/bot<TOKEN>/getUpdates` i odczytaj `chat.id` — to `TELEGRAM_CHAT_ID`.

### 2. Repozytorium GitHub
1. Wypchnij ten folder do nowego repo na GitHubie (może być prywatne).
2. W repo: **Settings → Secrets and variables → Actions → New repository secret**, dodaj:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - (opcjonalnie e-mail) `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_EMAIL`
     — dla Gmaila: `SMTP_HOST=smtp.gmail.com`, hasło to **App Password** (nie zwykłe hasło konta).
3. Zakładka **Actions** → włącz workflow, jeśli GitHub o to poprosi.

Workflow uruchomi się automatycznie co 5 minut. Możesz też odpalić go ręcznie przez
**Actions → Check iPhone 16e stock → Run workflow**.

## Uwagi
- To repo jest publiczne → GitHub Actions jest darmowe bez limitu minut niezależnie od częstotliwości
  (dla repo prywatnego byłby limit 2000 min/mies. w darmowym planie).
- GitHub automatycznie wyłącza harmonogram (`schedule`) po ~60 dniach bez aktywności w repo — wtedy
  wystarczy zrobić dowolny commit albo ręcznie uruchomić workflow, żeby go "obudzić".
- Amazon czasem pokazuje CAPTCHA przy zbyt częstych zapytaniach z jednego IP — skrypt to wykrywa
  (`reason="captcha/blocked"`) i po prostu pomija tę turę zamiast fałszywie alarmować. Jeśli to się
  zdarza często, zwiększ interwał crona (np. `*/15` zamiast `*/10`).
- SMS: nie ma sensownej darmowej i uniwersalnej bramki SMS (Twilio ma tylko ograniczony trial). Telegram
  na telefonie z powiadomieniami push działa praktycznie identycznie jak SMS i jest 100% darmowy.
