# iPhone 16e stock checker

Sprawdza co N minut, czy [iPhone 16e na Amazon.fr](https://www.amazon.fr/dp/B0DXQHPY34) jest dostępny,
i wysyła powiadomienie Telegram (+opcjonalnie e-mail), gdy pojawi się przycisk kupna.

## Jak to działa
- `check_stock.py` otwiera stronę produktu w headless Chromium (Playwright) i sprawdza tekst dostępności
  (`#availability`) oraz obecność przycisku `#buy-now-button` / `#add-to-cart-button`.
  **Zwykłe zapytania HTTP (`requests`) nie działają** — Amazon od razu pokazuje ekran
  "kliknij, aby kontynuować zakupy" zamiast strony produktu; prawdziwa przeglądarka to omija.
- GitHub Actions (`.github/workflows/check-stock.yml`) uruchamia skrypt za darmo — nie trzeba nic
  hostować (workflow doinstalowuje Chromium przy każdym uruchomieniu).
- Wbudowany trigger `schedule` w GitHub Actions okazał się **niewiarygodny** dla tego repo (potrafił nie
  odpalić się przez kilka godzin albo odpalać się nieregularnie zamiast co 5 min — to znane ograniczenie
  darmowego `schedule` dla mało aktywnych repo). Dlatego rzeczywistym "budzikiem" jest **zewnętrzny cron**
  (cron-job.org), który co 5 minut woła GitHub API i wymusza natychmiastowe uruchomienie workflow
  (`workflow_dispatch`) — patrz sekcja 3 poniżej. `schedule` zostaje w pliku jako dodatkowy, bonusowy
  trigger, ale nie jest już główną metodą.

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

Możesz też odpalić workflow ręcznie przez **Actions → Check iPhone 16e stock → Run workflow**.

### 3. Niezawodny "budzik" co 5 minut (cron-job.org)
Ponieważ wbudowany `schedule` GitHub Actions bywa nieregularny, prawdziwym harmonogramem jest zewnętrzny
serwis, który co 5 minut wywołuje GitHub API i wymusza uruchomienie:

1. Utwórz token: `github.com/settings/personal-access-tokens/new` → Repository access: tylko to repo →
   Permissions → **Actions: Read and write**.
2. Załóż darmowe konto na [cron-job.org](https://cron-job.org).
3. Utwórz zadanie cykliczne co 5 minut:
   - URL: `https://api.github.com/repos/<user>/<repo>/actions/workflows/check-stock.yml/dispatches`
   - Metoda: `POST`
   - Nagłówki: `Authorization: Bearer <TOKEN>`, `Accept: application/vnd.github+json`,
     `Content-Type: application/json`
   - Treść żądania (body): `{"ref":"main"}`
4. Test powinien zwrócić **204 No Content** — wtedy w zakładce Actions natychmiast pojawi się nowy run.

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
