import os
from config import Config


class ChurchReportFiller:
    def __init__(self, session, log=print):
        self.session = session
        self.log = log

    async def submit(self, row: dict) -> dict:
        acc = self.session.account_id
        result = {"account": acc, "type": "church", "date": row.get("event_date"),
                  "status": "failed", "error": None}
        page = self.session.page

        try:
            self.log(f"[{acc}] → Church Report form")
            await page.goto(Config.CHURCH_REPORT_URL, wait_until="networkidle")

            # ---- event date ----
            if row.get("event_date"):
                await page.fill('input[name="event_date"]', str(row["event_date"]))

            # ---- Yes/No radio (e.g. "Held on Sunday?") ----
            yn = str(row.get("name", "yes")).strip().lower()
            if yn in ("no", "n", "false", "0"):
                await page.check('#noCheck')
            else:
                await page.check('#yesCheck')

            # ---- Sunday 1 block ----
            await self._fill_number(page, '#CmisAttendance_1_adult',      row.get("sun1_adult"))
            await self._fill_number(page, '#CmisAttendance_1_children',   row.get("sun1_children"))
            await self._fill_number(page, '#CmisAttendance_1_childrenchurch', row.get("sun1_childrenchurch"))
            await self._fill_number(page, '#CmisAttendance_1_first_timers',   row.get("sun1_first_timers"))
            await self._fill_number(page, '#CmisAttendance_1_born_again',     row.get("sun1_born_again"))
            await self._fill_number(page, '#total1',                          row.get("sun1_total"))
            if row.get("sun1_testimonies"):
                # duplicate id — use name selector
                await page.fill(
                    'textarea[name="CmisAttendance[1][testimonies]"]',
                    str(row["sun1_testimonies"]),
                )

            # ---- Sunday 2 block ----
            await self._fill_number(page, '#CmisAttendance_2_adult',      row.get("sun2_adult"))
            await self._fill_number(page, '#CmisAttendance_2_children',   row.get("sun2_children"))
            await self._fill_number(page, '#CmisAttendance_2_childrenchurch', row.get("sun2_childrenchurch"))
            await self._fill_number(page, '#CmisAttendance_2_first_timers',   row.get("sun2_first_timers"))
            await self._fill_number(page, '#CmisAttendance_2_born_again',     row.get("sun2_born_again"))
            await self._fill_number(page, '#total2',                          row.get("sun2_total"))
            if row.get("sun2_testimonies"):
                await page.fill(
                    'textarea[name="CmisAttendance[2][testimonies]"]',
                    str(row["sun2_testimonies"]),
                )

            # ---- Midweek block ----
            await self._fill_number(page, '#wed_adult',        row.get("wed_adult"))
            await self._fill_number(page, '#wed_children',     row.get("wed_children"))
            await self._fill_number(page, '#childrenchurch',   row.get("wed_childrenchurch"))
            await self._fill_number(page, '#wed_first_timers', row.get("wed_first_timers"))
            await self._fill_number(page, '#wed_born_again',   row.get("wed_born_again"))
            await self._fill_number(page, '#wed_total',        row.get("wed_total"))
            if row.get("wed_testimonies"):
                await page.fill(
                    'textarea[name="CmisAttendance[testimonies]"]',
                    str(row["wed_testimonies"]),
                )

            # ---- Virtual church ----
            if row.get("virtual_platform"):
                await page.select_option('#platforms_used', label=str(row["virtual_platform"]))
            if row.get("virtual_link"):
                await page.fill('input[name="CmisAttendanceVirtual[1][platform_link]"]',
                                str(row["virtual_link"]))
            if row.get("virtual_service_pic"):
                path = self._resolve_file(row["virtual_service_pic"])
                if path:
                    await page.set_input_files(
                        'input[name="CmisAttendanceVirtual[1][platform_service_pic]"]', path)
            if row.get("virtual_counter_pic"):
                path = self._resolve_file(row["virtual_counter_pic"])
                if path:
                    await page.set_input_files(
                        'input[name="CmisAttendanceVirtual[1][platform_counter_pic]"]', path)
            await self._fill_number(page,
                'input[name="CmisAttendanceVirtual[1][platform_attendance]"]',
                row.get("virtual_attendance"))
            if row.get("virtual_testimony"):
                await page.fill(
                    'textarea[name="CmisAttendanceVirtual[1][testimony]"]',
                    str(row["virtual_testimony"]))
            await self._fill_number(page, '#virt_total', row.get("virtual_total"))

            # ---- Submit ----
            self.log(f"[{acc}] Submitting church report…")
            await page.click('input[name="yt0"]')
            await page.wait_for_load_state("networkidle")

            # Detect validation errors vs success
            if await page.locator('.error-summary, .has-error, .alert-danger').count() > 0:
                err_text = await page.locator('.error-summary, .has-error').first.inner_text()
                raise RuntimeError(f"Validation: {err_text[:200]}")

            result["status"] = "success"
            self.log(f"[{acc}] ✅ Church report saved for {row.get('event_date')}")

        except Exception as e:
            result["error"] = str(e)
            self.log(f"[{acc}] ❌ Church report failed: {e}")

        return result

    # ---- helpers ----
    async def _fill_number(self, page, selector, value):
        if value is None or value == "":
            return
        try:
            await page.fill(selector, str(value))
        except Exception:
            # Some fields might be readonly / auto-computed
            pass

    @staticmethod
    def _resolve_file(path_str):
        if not path_str:
            return None
        p = str(path_str).strip()
        if os.path.isabs(p) and os.path.exists(p):
            return p
        # relative → look under data/
        rel = os.path.join(Config.UPLOAD_FOLDER, p)
        return rel if os.path.exists(rel) else None