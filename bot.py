import io
import re
import sqlite3
import unicodedata
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = '8966364905:AAEJKwW7MFa7rV0oI53gtxKUZEiuTHp0_5M'
ADMIN_CHAT_ID = 8359903974         # ID Telegram Akun Utama / Admin
CS_USERNAME = 'bossgmailbotcs'    # ##.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            gmail TEXT UNIQUE,
            password TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            nominal INTEGER,
            metode TEXT,
            rekening TEXT,
            atas_nama TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TEXT
        )
    ''')
    
    cursor.execute("PRAGMA table_info(deposits)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'created_at' not in columns:
        cursor.execute("ALTER TABLE deposits ADD COLUMN created_at TEXT")

    cursor.execute("PRAGMA table_info(withdrawals)")
    wd_columns = [column[1] for column in cursor.fetchall()]
    if 'atas_nama' not in wd_columns:
        cursor.execute("ALTER TABLE withdrawals ADD COLUMN atas_nama TEXT")
        
    conn.commit()
    conn.close()

init_db()

# ----------------- KEYBOARD MENUS -----------------
def persistent_reply_keyboard():
    keyboard = [
        [KeyboardButton("🔄 Refresh / Start"), KeyboardButton("📜 Daftar Setoran Saya")],
        [KeyboardButton("💰 Cek Saldo"), KeyboardButton("💬 Hubungi CS")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def main_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("📥 Setor Satuan", callback_data="menu_satuan"),
            InlineKeyboardButton("📦 Setor Bulking", callback_data="menu_bulking")
        ],
        [
            InlineKeyboardButton("💰 Cek Saldo", callback_data="menu_saldo"),
            InlineKeyboardButton("💸 Penarikan Dana", callback_data="menu_tarik")
        ],
        [
            InlineKeyboardButton("📜 Riwayat Setoran", callback_data="menu_riwayat"),
            InlineKeyboardButton("🧾 Riwayat Withdraw", callback_data="menu_riwayat_wd")
        ],
        [
            InlineKeyboardButton("💬 Hubungi CS / Admin", url=f"https://t.me/{CS_USERNAME}")
        ]
    ]
    if user_id == ADMIN_CHAT_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Panel Admin", callback_data="admin_panel")])
        
    return InlineKeyboardMarkup(keyboard)

def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batal / Kembali ke Menu Utama", callback_data="menu_utama")]])

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali ke Menu Utama", callback_data="menu_utama")]])

# ----------------- PESAN SAMBUTAN UTAMA -----------------
def get_welcome_text(first_name):
    return (
        f"✨ *SELAMAT DATANG DI BOT SETORAN GMAIL V28* ✨\n"
        f"Halo *{first_name}*! Silakan baca informasi & aturan setoran di bawah ini:\n\n"
        f"💵 *INFORMASI RATE & PROSES*\n"
        f"• *Rate Per Akun:* Rp 4.000\n"
        f"• *Estimasi Pengecekan:* 24 - 48 Jam Kerja\n"
        f"• *Batas Bulking:* Maksimal {MAX_BULK_LIMIT} akun / setor\n\n"
        f"🔑 *ATURAN KATA SANDI (PASSWORD)*\n"
        f"• Password yang valid: `fineirga`, `sgsg1122`, atau `prabujaya`\n\n"
        f"⚠️ *SYARAT & KETENTUAN WAJIB*\n"
        f"1. *Dilarang Double-Sell:* Jangan pernah menjual kembali atau mengganti kata sandi akun selama proses verifikasi.\n"
        f"2. *Nomor HP Pemulihan:* Wajib dikosongkan / jangan diverifikasi.\n"
        f"3. *Kondisi Akun:* Akun langsung menampilkan opsi sandi (Good), bukan captcha.\n\n"
        f"👇 *Pilih menu di bawah ini untuk memulai:* "
    )

# ----------------- HANDLERS -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    context.user_data.clear()
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user.id, user.username))
    conn.commit()
    conn.close()

    await update.message.reply_text("Papan menu cepat diaktifkan di bawah 👇", reply_markup=persistent_reply_keyboard())
    await update.message.reply_text(get_welcome_text(user.first_name), reply_markup=main_menu_keyboard(user.id), parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    data = query.data
    user = query.from_user

    if data == "menu_utama":
        context.user_data.clear()
        await query.edit_message_text(get_welcome_text(user.first_name), reply_markup=main_menu_keyboard(user.id), parse_mode='Markdown')

    elif data == "menu_satuan":
        context.user_data['mode'] = 'SATUAN'
        pesan = (
            "⏳ *MODE SETORAN SATUAN AKTIF*\n"
            "═══════════════════════\n"
            "Silakan ketik dan kirimkan data Gmail kamu sekarang.\n\n"
            "📌 *Format:* `email@gmail.com:password`\n"
            "💡 *Password Wajib:* `fineirga` / `sgsg1122` / `prabujaya`\n"
            "💡 *Contoh:* `ridwan123@gmail.com:fineirga`\n\n"
            "_Sistem sedang menunggu inputan kamu..._"
        )
        await query.edit_message_text(pesan, reply_markup=cancel_keyboard(), parse_mode='Markdown')

    elif data == "menu_bulking":
        keyboard = [
            [InlineKeyboardButton("🔑 fineirga", callback_data="bulkpwd_fineirga")],
            [InlineKeyboardButton("🔑 sgsg1122", callback_data="bulkpwd_sgsg1122")],
            [InlineKeyboardButton("🔑 prabujaya", callback_data="bulkpwd_prabujaya")],
            [InlineKeyboardButton("« Batal / Kembali", callback_data="menu_utama")]
        ]
        pesan = (
            "📦 *SETORAN BULKING - PILIH PASSWORD*\n"
            "═══════════════════════\n"
            "Silakan pilih kata sandi yang digunakan untuk kelompok akun yang ingin kamu setor:"
        )
        await query.edit_message_text(pesan, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data.startswith("bulkpwd_"):
        chosen_password = data.split('_')[1]
        context.user_data['mode'] = 'BULKING_INPUT_EMAILS'
        context.user_data['bulk_password'] = chosen_password

        pesan = (
            f"📦 *SETORAN BULKING AKTIF*\n"
            f"═══════════════════════\n"
            f"🔑 *Password Dipilih:* `{chosen_password}`\n"
            f"⚠️ *Batas Maksimal:* {MAX_BULK_LIMIT} Akun sekali kirim\n\n"
            f"Sekarang, silakan *ketik atau paste daftar list gmail* dengan format awal (`email@gmail.com` atau `email@gmail.com:password`) di bawah ini (satu per baris):\n\n"
            f"📌 *Contoh Format:*\n"
            f"`email1@gmail.com`\n"
            f"`email2@gmail.com`\n\n"
            f"_Sistem sedang menunggu list kamu..._"
        )
        await query.edit_message_text(pesan, reply_markup=cancel_keyboard(), parse_mode='Markdown')

    elif data == "menu_saldo":
        context.user_data.clear()
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM deposits WHERE user_id = ? AND status = "APPROVED"', (user.id,))
        app_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM deposits WHERE user_id = ? AND status = "PENDING"', (user.id,))
        pen_count = cursor.fetchone()[0]

        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user.id,))
        res = cursor.fetchone()
        balance_ready = res[0] if res else 0

        conn.close()

        pesan = (
            f"📊 *INFORMASI AKUN & SALDO*\n"
            f"═══════════════════════\n"
            f"💵 *Saldo Dapat Dicairkan:* Rp {balance_ready:,}\n"
            f"⏳ *Saldo Tertahan (Pending):* Rp {pen_count * HARGA_PER_GMAIL:,}\n"
            f"═══════════════════════\n"
            f"✅ *Gmail Disetujui (Approved):* {app_count} Akun\n"
            f"⏳ *Gmail Menunggu (Pending):* {pen_count} Akun\n"
            f"═══════════════════════"
        )
        await query.edit_message_text(pesan, reply_markup=back_keyboard(), parse_mode='Markdown')

    elif data == "menu_riwayat":
        context.user_data.clear()
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT gmail, status, created_at FROM deposits WHERE user_id = ? ORDER BY id DESC LIMIT 15', (user.id,))
        items = cursor.fetchall()
        conn.close()

        if not items:
            pesan = "📜 *DAFTAR SETORAN GMAIL*\n═══════════════════════\nBelum ada riwayat setoran."
        else:
            pesan = "📜 *DAFTAR SETORAN GMAIL (15 Terakhir)*\n═══════════════════════\n"
            for g_mail, st, dt in items:
                status_icon = "⌛ PENDING"
                if st == "APPROVED":
                    status_icon = "✅ APPROVED"
                elif st == "REJECTED":
                    status_icon = "❌ REJECTED"
                
                waktu = dt if dt else datetime.now().strftime("%d-%m-%Y %H:%M:%S WIB")
                pesan += f"📧 `{g_mail}`\n└ Status: *{status_icon}*\n└ Waktu: `{waktu}`\n\n"

        await query.edit_message_text(pesan, reply_markup=back_keyboard(), parse_mode='Markdown')

    elif data == "menu_riwayat_wd":
        context.user_data.clear()
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nominal, metode, rekening, atas_nama, status, created_at FROM withdrawals WHERE user_id = ? ORDER BY id DESC LIMIT 10', (user.id,))
        wd_items = cursor.fetchall()
        conn.close()

        if not wd_items:
            pesan = "🧾 *RIWAYAT PENARIKAN DANA*\n═══════════════════════\nBelum ada riwayat penarikan dana."
        else:
            pesan = "🧾 *RIWAYAT PENARIKAN DANA (10 Terakhir)*\n═══════════════════════\n"
            for w_id, nom, met, rek, an, st, dt in wd_items:
                status_icon = "⌛ PENDING"
                if st == "APPROVED":
                    status_icon = "✅ BERHASIL"
                elif st == "REJECTED":
                    status_icon = "❌ DITOLAK (REFUND)"

                waktu = dt if dt else "-"
                pesan += (
                    f"🆔 *ID WD:* `#WD{w_id}`\n"
                    f"💵 *Nominal:* Rp {nom:,}\n"
                    f"🏦 *Metode:* {met} (`{rek}`)\n"
                    f"👤 *A/N:* `{an}`\n"
                    f"📌 *Status:* *{status_icon}*\n"
                    f"🕒 *Waktu:* `{waktu}`\n"
                    f"───────────────────────\n"
                )

        await query.edit_message_text(pesan, reply_markup=back_keyboard(), parse_mode='Markdown')

    elif data == "menu_tarik":
        context.user_data.clear()
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user.id,))
        res = cursor.fetchone()
        balance = res[0] if res else 0
        conn.close()

        if balance < HARGA_PER_GMAIL:
            pesan = (
                f"💸 *PENARIKAN DANA*\n"
                f"═══════════════════════\n"
                f"💰 *Saldo Dapat Dicairkan:* Rp {balance:,}\n\n"
                f"⚠️ *Minimal penarikan dana adalah Rp {HARGA_PER_GMAIL:,} (Harga 1 Akun).* Saldo kamu belum mencukupi."
            )
            await query.edit_message_text(pesan, reply_markup=back_keyboard(), parse_mode='Markdown')
            return

        nominals = [4000, 8000, 12000, 20000, 50000, 100000]
        keyboard = []
        for n in nominals:
            if balance >= n:
                keyboard.append([InlineKeyboardButton(f"💵 Rp {n:,}", callback_data=f"wdnom_{n}")])
        keyboard.append([InlineKeyboardButton(f"🔥 Semua Saldo (Rp {balance:,})", callback_data=f"wdnom_{balance}")])
        keyboard.append([InlineKeyboardButton("« Kembali ke Menu Utama", callback_data="menu_utama")])

        pesan = (
            f"💸 *PENARIKAN DANA INTERAKTIF*\n"
            f"═══════════════════════\n"
            f"💰 *Saldo Dapat Dicairkan:* Rp {balance:,}\n\n"
            f"Pilih nominal pencairan yang kamu inginkan di bawah ini:"
        )
        await query.edit_message_text(pesan, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data.startswith("wdnom_"):
        nominal = int(data.split('_')[1])
        context.user_data['wd_nominal'] = nominal

        methods = ["DANA", "OVO", "GoPay", "ShopeePay", "BCA", "BRI", "Mandiri", "BNI"]
        keyboard = []
        for i in range(0, len(methods), 2):
            row = [InlineKeyboardButton(methods[i], callback_data=f"wdmet_{methods[i]}")]
            if i + 1 < len(methods):
                row.append(InlineKeyboardButton(methods[i+1], callback_data=f"wdmet_{methods[i+1]}"))
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("« Batal", callback_data="menu_utama")])

        pesan = (
            f"💳 *PILIH METODE PEMBAYARAN*\n"
            f"═══════════════════════\n"
            f"💵 *Nominal Penarikan:* Rp {nominal:,}\n\n"
            f"Silakan pilih metode pencairan dana:"
        )
        await query.edit_message_text(pesan, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data.startswith("wdmet_"):
        metode = data.split('_')[1]
        nominal = context.user_data.get('wd_nominal', 0)
        context.user_data['wd_metode'] = metode
        context.user_data['mode'] = 'WAITING_REK'

        pesan = (
            f"📝 *INPUT NOMOR REKENING / HP*\n"
            f"═══════════════════════\n"
            f"💵 *Nominal:* Rp {nominal:,}\n"
            f"🏦 *Metode:* {metode}\n\n"
            f"Silakan *ketik dan kirimkan* Nomor Rekening / E-Wallet kamu sekarang:"
        )
        await query.edit_message_text(pesan, reply_markup=cancel_keyboard(), parse_mode='Markdown')

    elif data == "admin_panel":
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        keyboard = [
            [InlineKeyboardButton("⚙️ Kelola Setoran Gmail Pending", callback_data="admin_setoran")],
            [InlineKeyboardButton("💸 Kelola Withdraw Pending", callback_data="admin_withdraw")],
            [InlineKeyboardButton("« Kembali ke Menu Utama", callback_data="menu_utama")]
        ]

        pesan = "⚙️ *PANEL ADMIN*\n═══════════════════════\nSilakan pilih menu pengelola di bawah ini:"
        await query.edit_message_text(pesan, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data == "admin_setoran":
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        # Query yang menjamin data setoran PENDING selalu ditarik permanen dari DB
        cursor.execute('''
            SELECT deposits.user_id, users.username, COUNT(*) 
            FROM deposits 
            LEFT JOIN users ON deposits.user_id = users.user_id 
            WHERE deposits.status = "PENDING" 
            GROUP BY deposits.user_id
        ''')
        user_list = cursor.fetchall()
        conn.close()

        if not user_list:
            await query.edit_message_text("✅ *Tidak ada setoran pending saat ini.*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali ke Panel Admin", callback_data="admin_panel")]]), parse_mode='Markdown')
            return

        keyboard = []
        for target_uid, uname, cnt in user_list:
            u_text = f"@{uname}" if uname else f"ID: {target_uid}"
            keyboard.append([InlineKeyboardButton(f"👤 {u_text} ({cnt} Akun)", callback_data=f"admuser_{target_uid}")])
        
        keyboard.append([InlineKeyboardButton("« Kembali ke Panel Admin", callback_data="admin_panel")])

        pesan = (
            f"⚙️ *PANEL ADMIN - KELOLA SETORAN PENDING*\n"
            f"═══════════════════════\n"
            f"Pilih user di bawah ini untuk melihat dan mengelola daftar akun:"
        )
        await query.edit_message_text(pesan, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data == "admin_withdraw":
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT w.id, w.user_id, u.username, w.nominal, w.metode, w.rekening, w.atas_nama, w.created_at 
            FROM withdrawals w 
            LEFT JOIN users u ON w.user_id = u.user_id 
            WHERE w.status = "PENDING" 
            ORDER BY w.id DESC
        ''')
        wd_list = cursor.fetchall()
        conn.close()

        if not wd_list:
            await query.edit_message_text("✅ *Tidak ada permintaan withdraw pending.*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali ke Panel Admin", callback_data="admin_panel")]]), parse_mode='Markdown')
            return

        pesan = f"💸 *DAFTAR PERMINTAAN WITHDRAW PENDING*\n═══════════════════════\n\n"
        keyboard = []
        for wd_id, uid, uname, nom, met, rek, an, dt in wd_list:
            u_txt = f"@{uname}" if uname else f"ID: `{uid}`"
            pesan += (
                f"🆔 *ID WD:* `#WD{wd_id}`\n"
                f"👤 *User:* {u_txt}\n"
                f"💵 *Nominal:* Rp {nom:,}\n"
                f"🏦 *Metode:* {met}\n"
                f"📌 *No Rek/HP:* `{rek}`\n"
                f"👤 *A/N:* `{an}`\n"
                f"🕒 *Waktu:* `{dt}`\n\n"
            )
            keyboard.append([
                InlineKeyboardButton(f"✅ Approve #WD{wd_id}", callback_data=f"accwd_{wd_id}"),
                InlineKeyboardButton(f"❌ Reject #WD{wd_id}", callback_data=f"rejwd_{wd_id}")
            ])

        keyboard.append([InlineKeyboardButton("« Kembali ke Panel Admin", callback_data="admin_panel")])
        await query.edit_message_text(pesan, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data.startswith("admuser_"):
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        target_uid = int(data.split('_')[1])
        context.user_data['sel_target_uid'] = target_uid
        context.user_data['selected_deps'] = []

        await render_admin_user_deposits(query, target_uid, context)

    elif data.startswith("pasterej_ask_"):
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        target_uid = int(data.split('_')[2])
        context.user_data['sel_target_uid'] = target_uid

        keyboard = []
        for idx, reason in enumerate(REJECT_REASONS):
            keyboard.append([InlineKeyboardButton(f"❌ {reason}", callback_data=f"pasterej_do_{target_uid}_{idx}")])
        keyboard.append([InlineKeyboardButton("« Kembali ke User", callback_data=f"admuser_{target_uid}")])

        pesan = (
            f"❌ *REJECT PASTE LIST (User ID: `{target_uid}`)*\n"
            f"═══════════════════════\n"
            f"Pilih alasan penolakan terlebih dahulu sebelum Anda mengirimkan teks/list email yang ingin direject:"
        )
        await query.edit_message_text(pesan, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data.startswith("pasterej_do_"):
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        parts = data.split('_')
        target_uid = int(parts[2])
        reason_idx = int(parts[3])

        context.user_data['sel_target_uid'] = target_uid
        context.user_data['paste_reject_reason_idx'] = reason_idx
        context.user_data['mode'] = 'WAITING_USER_PASTE_REJECT'
        chosen_reason = REJECT_REASONS[reason_idx] if reason_idx < len(REJECT_REASONS) else "Ditolak Admin"

        pesan = (
            f"❌ *KIRIM DAFTAR EMAIL YANG DI-REJECT*\n"
            f"═══════════════════════\n"
            f"👤 *Target User:* `{target_uid}`\n"
            f"📌 *Alasan Dipilih:* {chosen_reason}\n\n"
            f"Sekarang, silakan *ketik atau paste* daftar email milik user ini yang ingin di-reject (satu email per baris)."
        )
        await query.edit_message_text(pesan, reply_markup=cancel_keyboard(), parse_mode='Markdown')

    elif data.startswith("togdep_"):
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        dep_id = int(data.split('_')[1])
        target_uid = context.user_data.get('sel_target_uid')
        if not target_uid:
            return

        selected_deps = context.user_data.setdefault('selected_deps', [])
        if dep_id in selected_deps:
            selected_deps.remove(dep_id)
        else:
            selected_deps.append(dep_id)

        await render_admin_user_deposits(query, target_uid, context)

    elif data == "togall_deps":
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        target_uid = context.user_data.get('sel_target_uid')
        if not target_uid:
            return

        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM deposits WHERE user_id = ? AND status = "PENDING"', (target_uid,))
        all_items = [row[0] for row in cursor.fetchall()]
        conn.close()

        selected_deps = context.user_data.setdefault('selected_deps', [])
        if len(selected_deps) == len(all_items):
            context.user_data['selected_deps'] = []
        else:
            context.user_data['selected_deps'] = all_items

        await render_admin_user_deposits(query, target_uid, context)

    elif data == "do_sel_approve":
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        target_uid = context.user_data.get('sel_target_uid')
        selected_deps = context.user_data.get('selected_deps', [])

        if not selected_deps:
            await query.answer("⚠️ Belum ada akun yang dicentang!", show_alert=True)
            return

        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(selected_deps))
        cursor.execute(f'UPDATE deposits SET status = "APPROVED" WHERE id IN ({placeholders})', selected_deps)
        
        count = len(selected_deps)
        total_added = count * HARGA_PER_GMAIL
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (total_added, target_uid))
        conn.commit()
        conn.close()

        context.user_data['selected_deps'] = []
        await query.edit_message_text(
            f"✅ *APPROVE TERPILIH BERHASIL!*\n\nTotal `{count}` akun dari User `{target_uid}` telah disetujui.\nSaldo +Rp {total_added:,} telah dikreditkan.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali ke Daftar User", callback_data="admin_setoran")]]),
            parse_mode='Markdown'
        )

        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text=f"🎉 *SETORAN DI-APPROVE!*\n\nSebanyak *{count} akun Gmail* kamu telah diverifikasi dan disetujui oleh admin.\n💰 *+Rp {total_added:,}* telah masuk ke saldo cair kamu!",
                parse_mode='Markdown'
            )
        except Exception:
            pass

    elif data == "do_sel_reject_ask":
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        selected_deps = context.user_data.get('selected_deps', [])
        if not selected_deps:
            await query.answer("⚠️ Belum ada akun yang dicentang!", show_alert=True)
            return

        keyboard = []
        for idx, reason in enumerate(REJECT_REASONS):
            keyboard.append([InlineKeyboardButton(f"❌ {reason}", callback_data=f"do_sel_rej_{idx}")])
        keyboard.append([InlineKeyboardButton("« Batal", callback_data=f"admuser_{context.user_data.get('sel_target_uid')}")])

        pesan = f"⚠️ *PILIH ALASAN PENOLAKAN UNTUK {len(selected_deps)} AKUN TERPILIH*"
        await query.edit_message_text(pesan, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data.startswith("do_sel_rej_"):
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        reason_idx = int(data.split('_')[3])
        chosen_reason = REJECT_REASONS[reason_idx] if reason_idx < len(REJECT_REASONS) else "Ditolak Admin"

        target_uid = context.user_data.get('sel_target_uid')
        selected_deps = context.user_data.get('selected_deps', [])

        if not selected_deps:
            await query.edit_message_text("⚠️ Tidak ada akun terpilih.", reply_markup=back_keyboard())
            return

        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(selected_deps))
        cursor.execute(f'SELECT gmail FROM deposits WHERE id IN ({placeholders})', selected_deps)
        rejected_emails = [row[0] for row in cursor.fetchall()]

        cursor.execute(f'UPDATE deposits SET status = "REJECTED" WHERE id IN ({placeholders})', selected_deps)
        conn.commit()
        conn.close()

        count = len(selected_deps)
        context.user_data['selected_deps'] = []

        await query.edit_message_text(
            f"❌ *REJECT TERPILIH BERHASIL!*\n\nTotal `{count}` akun dari User `{target_uid}` telah ditolak.\n📌 *Alasan:* {chosen_reason}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali ke Daftar User", callback_data="admin_setoran")]]),
            parse_mode='Markdown'
        )

        try:
            email_list_str = "\n".join([f"• `{e}`" for e in rejected_emails])
            await context.bot.send_message(
                chat_id=target_uid,
                text=(
                    f"❌ *PEMBERITAHUAN PENOLAKAN GMAIL*\n"
                    f"═══════════════════════\n"
                    f"⚠️ Sejumlah {count} akun setoran Anda ditolak:\n"
                    f"{email_list_str}\n\n"
                    f"📌 *Alasan Ditolak:* {chosen_reason}\n"
                    f"═══════════════════════\n"
                    f"Silakan periksa kembali akun Anda."
                ),
                parse_mode='Markdown'
            )
        except Exception:
            pass

    elif data.startswith("accwd_"):
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        wd_id = int(data.split('_')[1])
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, nominal, metode, rekening, atas_nama, status FROM withdrawals WHERE id = ?', (wd_id,))
        res = cursor.fetchone()

        if not res or res[5] != 'PENDING':
            await query.edit_message_text("⚠️ Penarikan ini sudah diproses.", reply_markup=back_keyboard())
            conn.close()
            return

        target_uid, nominal, metode, rekening, atas_nama, _ = res
        cursor.execute('UPDATE withdrawals SET status = "APPROVED" WHERE id = ?', (wd_id,))
        conn.commit()
        conn.close()

        await query.edit_message_text(
            f"✅ *PENARIKAN #WD{wd_id} APPROVED!*\n\nNominal: Rp {nominal:,}\nMetode: {metode}\nRek/HP: `{rekening}`\nA/N: `{atas_nama}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali ke Panel WD", callback_data="admin_withdraw")]]),
            parse_mode='Markdown'
        )

        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text=(
                    f"🎉 *PENARIKAN DANA BERHASIL!*\n"
                    f"═══════════════════════\n"
                    f"🆔 *ID WD:* `#WD{wd_id}`\n"
                    f"💵 *Nominal:* Rp {nominal:,}\n"
                    f"🏦 *Metode:* {metode}\n"
                    f"📌 *No Rek/HP:* `{rekening}`\n"
                    f"👤 *A/N:* `{atas_nama}`\n"
                    f"═══════════════════════\n"
                    f"Dana telah berhasil ditransfer ke rekening/e-wallet kamu. Terima kasih!"
                ),
                parse_mode='Markdown'
            )
        except Exception:
            pass

    elif data.startswith("rejwd_"):
        if user.id != ADMIN_CHAT_ID:
            await query.answer("❌ Akses khusus Admin!", show_alert=True)
            return

        wd_id = int(data.split('_')[1])
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, nominal, metode, rekening, atas_nama, status FROM withdrawals WHERE id = ?', (wd_id,))
        res = cursor.fetchone()

        if not res or res[5] != 'PENDING':
            await query.edit_message_text("⚠️ Penarikan ini sudah diproses.", reply_markup=back_keyboard())
            conn.close()
            return

        target_uid, nominal, metode, rekening, atas_nama, _ = res
        cursor.execute('UPDATE withdrawals SET status = "REJECTED" WHERE id = ?', (wd_id,))
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (nominal, target_uid))
        conn.commit()
        conn.close()

        await query.edit_message_text(
            f"❌ *PENARIKAN #WD{wd_id} DITOLAK & SALDO DIREFUND!*\n\nNominal Rp {nominal:,} dikembalikan ke User `{target_uid}`.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali ke Panel WD", callback_data="admin_withdraw")]]),
            parse_mode='Markdown'
        )

        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text=(
                    f"❌ *PENARIKAN DANA DITOLAK*\n"
                    f"═══════════════════════\n"
                    f"🆔 *ID WD:* `#WD{wd_id}`\n"
                    f"💵 *Nominal:* Rp {nominal:,}\n"
                    f"🏦 *Metode:* {metode}\n"
                    f"📌 *No Rek/HP:* `{rekening}`\n"
                    f"👤 *A/N:* `{atas_nama}`\n"
                    f"═══════════════════════\n"
                    f"Permintaan penarikan kamu ditolak oleh admin.\n"
                    f"💰 *Saldo sebesar Rp {nominal:,} telah dikembalikan (refund) secara otomatis ke akun kamu.*"
                ),
                parse_mode='Markdown'
            )
        except Exception:
            pass

async def render_admin_user_deposits(query, target_uid, context):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, gmail, password, created_at FROM deposits WHERE user_id = ? AND status = "PENDING"', (target_uid,))
    items = cursor.fetchall()
    conn.close()

    if not items:
        await query.edit_message_text("✅ *Tidak ada setoran pending untuk user ini.*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali ke Daftar User", callback_data="admin_setoran")]]), parse_mode='Markdown')
        return

    selected_deps = context.user_data.get('selected_deps', [])

    pesan = f"📧 *PILIH AKUN GMAIL (User ID: `{target_uid}`)*\n═══════════════════════\nSilakan centang akun yang ingin diproses:\n\n"
    keyboard = []

    for dep_id, g_mail, p_ass, dt in items:
        is_checked = dep_id in selected_deps
        check_icon = "✅ [PILIH]" if is_checked else "⬜ [   ]"
        
        pesan += f"{check_icon} `{g_mail}` | `{p_ass}`\n"
        keyboard.append([InlineKeyboardButton(f"{check_icon} {g_mail}", callback_data=f"togdep_{dep_id}")])

    keyboard.append([InlineKeyboardButton("☑️ Pilih / Batalkan Semua", callback_data="togall_deps")])
    keyboard.append([InlineKeyboardButton("📋 Reject via Paste List untuk User Ini", callback_data=f"pasterej_ask_{target_uid}")])
    keyboard.append([
        InlineKeyboardButton(f"✅ Approve Terpilih ({len(selected_deps)})", callback_data="do_sel_approve"),
        InlineKeyboardButton(f"❌ Reject Terpilih ({len(selected_deps)})", callback_data="do_sel_reject_ask")
    ])
    keyboard.append([InlineKeyboardButton("« Kembali ke Daftar User", callback_data="admin_setoran")])

    try:
        await query.edit_message_text(pesan, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception:
        pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.message.from_user
    current_mode = context.user_data.get('mode')

    if text in ["🔄 Refresh / Start", "/start"]:
        await start(update, context)
        return
    elif text == "📜 Daftar Setoran Saya":
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT gmail, status, created_at FROM deposits WHERE user_id = ? ORDER BY id DESC LIMIT 15', (user.id,))
        items = cursor.fetchall()
        conn.close()

        if not items:
            pesan = "📜 *DAFTAR SETORAN GMAIL*\n═══════════════════════\nBelum ada riwayat setoran."
        else:
            pesan = "📜 *DAFTAR SETORAN GMAIL (15 Terakhir)*\n═══════════════════════\n"
            for g_mail, st, dt in items:
                status_icon = "⌛ PENDING"
                if st == "APPROVED":
                    status_icon = "✅ APPROVED"
                elif st == "REJECTED":
                    status_icon = "❌ REJECTED"
                
                waktu = dt if dt else datetime.now().strftime("%d-%m-%Y %H:%M:%S WIB")
                pesan += f"📧 `{g_mail}`\n└ Status: *{status_icon}*\n└ Waktu: `{waktu}`\n\n"

        await update.message.reply_text(pesan, reply_markup=back_keyboard(), parse_mode='Markdown')
        return
    elif text == "💰 Cek Saldo":
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM deposits WHERE user_id = ? AND status = "APPROVED"', (user.id,))
        app_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM deposits WHERE user_id = ? AND status = "PENDING"', (user.id,))
        pen_count = cursor.fetchone()[0]
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user.id,))
        res = cursor.fetchone()
        balance_ready = res[0] if res else 0
        conn.close()

        pesan = (
            f"📊 *INFORMASI AKUN & SALDO*\n"
            f"═══════════════════════\n"
            f"💵 *Saldo Dapat Dicairkan:* Rp {balance_ready:,}\n"
            f"⏳ *Saldo Tertahan (Pending):* Rp {pen_count * HARGA_PER_GMAIL:,}\n"
            f"═══════════════════════\n"
            f"✅ *Gmail Disetujui:* {app_count} Akun\n"
            f"⏳ *Gmail Menunggu:* {pen_count} Akun\n"
            f"═══════════════════════"
        )
        await update.message.reply_text(pesan, reply_markup=back_keyboard(), parse_mode='Markdown')
        return
    elif text == "💬 Hubungi CS":
        await update.message.reply_text(
            f"💬 Silakan hubungi Customer Service kami di: @{CS_USERNAME}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Chat CS Sekarang", url=f"https://t.me/{CS_USERNAME}")]])
        )
        return

    # Pembersihan Total Karakter Tersembunyi
    text_normalized = unicodedata.normalize("NFKD", text)
    cleaned_text = "".join([c for c in text_normalized if not unicodedata.combining(c)])
    cleaned_text = cleaned_text.replace('\r', '').replace('\ufeff', '').replace('\u200b', '')
    
    raw_lines = cleaned_text.split('\n')
    lines = [line.strip() for line in raw_lines if line.strip()]

    if current_mode == 'WAITING_USER_PASTE_REJECT':
        if user.id != ADMIN_CHAT_ID:
            return

        target_uid = context.user_data.get('sel_target_uid')
        reason_idx = context.user_data.get('paste_reject_reason_idx', 0)
        chosen_reason = REJECT_REASONS[reason_idx] if reason_idx < len(REJECT_REASONS) else "Ditolak Admin"

        emails_to_reject = []
        for line in lines:
            line_lower = line.lower()
            if ':' in line_lower:
                part = line_lower.split(':')[0].strip()
                if '@gmail.com' in part:
                    emails_to_reject.append(part)
            elif '@gmail.com' in line_lower:
                emails_to_reject.append(line_lower)

        if not emails_to_reject:
            await update.message.reply_text(
                "❌ *Format email tidak valid atau tidak ditemukan.*\nSilakan kirim ulang daftar email yang benar atau klik batal.",
                reply_markup=cancel_keyboard(),
                parse_mode='Markdown'
            )
            return

        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()

        success_count = 0
        not_found_count = 0
        actually_rejected_emails = []

        for email in emails_to_reject:
            cursor.execute('SELECT id FROM deposits WHERE user_id = ? AND gmail = ? AND status = "PENDING"', (target_uid, email))
            row = cursor.fetchone()
            
            if row:
                dep_id = row[0]
                cursor.execute('UPDATE deposits SET status = "REJECTED" WHERE id = ?', (dep_id,))
                success_count += 1
                actually_rejected_emails.append(email)
            else:
                not_found_count += 1

        conn.commit()
        conn.close()

        if actually_rejected_emails:
            try:
                email_list_str = "\n".join([f"• `{e}`" for e in actually_rejected_emails])
                await context.bot.send_message(
                    chat_id=target_uid,
                    text=(
                        f"❌ *PEMBERITAHUAN PENOLAKAN GMAIL*\n"
                        f"═══════════════════════\n"
                        f"⚠️ Sejumlah {len(actually_rejected_emails)} akun setoran Anda ditolak:\n"
                        f"{email_list_str}\n\n"
                        f"📌 *Alasan Ditolak:* {chosen_reason}\n"
                        f"═══════════════════════\n"
                        f"Silakan periksa kembali akun Anda."
                    ),
                    parse_mode='Markdown'
                )
            except Exception:
                pass

        context.user_data.clear()
        await update.message.reply_text(
            f"✅ *REJECT PASTE LIST BERHASIL!*\n\n"
            f"• Berhasil di-reject & dinotifikasi ke user: `{success_count}` akun\n"
            f"• Tidak cocok / tidak ditemukan di list pending user ini: `{not_found_count}` akun\n"
            f"• Alasan: {chosen_reason}",
            reply_markup=main_menu_keyboard(user.id),
            parse_mode='Markdown'
        )
        return

    if current_mode == 'WAITING_REK':
        context.user_data['wd_rekening'] = text
        context.user_data['mode'] = 'WAITING_AN'

        pesan = (
            f"👤 *INPUT NAMA ATAS NAMA (A/N)*\n"
            f"═══════════════════════\n"
            f"📌 *No Rek/HP:* `{text}`\n\n"
            f"Silakan *ketik dan kirimkan Nama Pemilik (Atas Nama)* dari rekening/e-wallet kamu:"
        )
        await update.message.reply_text(pesan, reply_markup=cancel_keyboard(), parse_mode='Markdown')
        return

    elif current_mode == 'WAITING_AN':
        atas_nama = text
        rekening = context.user_data.get('wd_rekening', '-')
        nominal = context.user_data.get('wd_nominal', 0)
        metode = context.user_data.get('wd_metode', '-')

        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user.id,))
        res = cursor.fetchone()
        balance = res[0] if res else 0

        if balance < nominal:
            await update.message.reply_text("❌ Saldo tidak mencukupi untuk melakukan penarikan ini.", reply_markup=main_menu_keyboard(user.id))
            context.user_data.clear()
            conn.close()
            return

        now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S WIB")
        cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (nominal, user.id))
        cursor.execute('INSERT INTO withdrawals (user_id, nominal, metode, rekening, atas_nama, created_at) VALUES (?, ?, ?, ?, ?, ?)', 
                       (user.id, nominal, metode, rekening, atas_nama, now_str))
        wd_id = cursor.lastrowid
        conn.commit()
        conn.close()

        username_txt = f"@{user.username}" if user.username else "No Username"
        keyboard_admin = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"✅ Approve #WD{wd_id}", callback_data=f"accwd_{wd_id}"),
                InlineKeyboardButton(f"❌ Reject #WD{wd_id} (Refund)", callback_data=f"rejwd_{wd_id}")
            ]
        ])

        laporan_admin = (
            f"💸 *PERMINTAAN PENARIKAN DANA*\n"
            f"═══════════════════════\n"
            f"🆔 *ID WD:* `#WD{wd_id}`\n"
            f"👤 *Pengirim:* {user.first_name} ({username_txt})\n"
            f"🆔 *ID Telegram:* `{user.id}`\n"
            f"💵 *Nominal:* Rp {nominal:,}\n"
            f"🏦 *Metode:* {metode}\n"
            f"📌 *No Rek/HP:* `{rekening}`\n"
            f"👤 *A/N:* `{atas_nama}`\n"
            f"🕒 *Waktu:* `{now_str}`\n"
            f"═══════════════════════"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=laporan_admin, reply_markup=keyboard_admin, parse_mode='Markdown')
        except Exception:
            pass

        context.user_data.clear()
        await update.message.reply_text(
            f"✅ *PENARIKAN BERHASIL DIAJUKAN!*\n\n"
            f"🆔 ID WD: `#WD{wd_id}`\n"
            f"💵 Nominal: *Rp {nominal:,}*\n"
            f"🏦 Metode: *{metode}*\n"
            f"📌 No Rek/HP: `{rekening}`\n"
            f"👤 Atas Nama: `{atas_nama}`\n\n"
            f"Permintaan penarikan kamu sedang diproses oleh admin. Cek statusnya secara berkala melalui menu *Riwayat Withdraw*.",
            reply_markup=main_menu_keyboard(user.id),
            parse_mode='Markdown'
        )
        return

    if not current_mode:
        await update.message.reply_text(
            "⚠️ Silakan pilih tombol **Setor Satuan** atau **Setor Bulking** terlebih dahulu pada menu utama.",
            reply_markup=main_menu_keyboard(user.id),
            parse_mode='Markdown'
        )
        return

    items_to_process = []
    is_bulking_mode = (current_mode == 'BULKING_INPUT_EMAILS')
    bulk_password_used = context.user_data.get('bulk_password') if is_bulking_mode else None

    if current_mode == 'SATUAN':
        satuan_pattern = r'([a-zA-Z0-9._%+-]+@gmail\.com)\s*:\s*(.+)'
        for line in lines:
            match = re.match(satuan_pattern, line, re.IGNORECASE)
            if match:
                items_to_process.append((match.group(1).lower(), match.group(2)))

    elif is_bulking_mode:
        for line in lines:
            line_clean = line.strip()
            if '@gmail.com' in line_clean.lower():
                if ':' in line_clean:
                    extracted_email = line_clean.split(':')[0].strip().lower()
                else:
                    extracted_email = line_clean.lower()
                
                if extracted_email.endswith('@gmail.com'):
                    items_to_process.append((extracted_email, bulk_password_used))

        total_input_count = len(items_to_process)
        if total_input_count > MAX_BULK_LIMIT:
            items_to_process = items_to_process[:MAX_BULK_LIMIT]

    if items_to_process:
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user.id, user.username))
        
        inserted_count = 0
        duplicate_count = 0
        successfully_inserted_accounts = []

        for gmail, password in items_to_process:
            cursor.execute('SELECT id FROM deposits WHERE gmail = ?', (gmail,))
            if cursor.fetchone():
                duplicate_count += 1
                continue

            now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S WIB")

            cursor.execute('INSERT INTO deposits (user_id, gmail, password, created_at) VALUES (?, ?, ?, ?)', (user.id, gmail, password, now_str))
            conn.commit()
            inserted_count += 1
            successfully_inserted_accounts.append((gmail, password))

        conn.close()
        context.user_data.clear()

        if inserted_count > 0:
            username_txt = f"@{user.username}" if user.username else "No Username"
            mode_label = "BULKING" if is_bulking_mode else "SATUAN"
            
            # 1. Teks Notifikasi Pesan Singkat
            laporan_admin_text = (
                f"📥 *SETORAN {mode_label} BARU MASUK*\n"
                f"═══════════════════════\n"
                f"👤 *User:* {user.first_name} ({username_txt})\n"
                f"🆔 *ID User:* `{user.id}`\n"
                f"📦 *Jumlah Akun:* `{inserted_count}` Akun Gmail\n"
                f"═══════════════════════\n"
                f"📄 *Data akun dikirim dalam bentuk file .txt di bawah ini.*"
            )

            # 2. Pembuatan File .txt dalam Memory
            txt_content = "\n".join([f"{g}:{p}" for g, p in successfully_inserted_accounts])
            txt_file = io.BytesIO(txt_content.encode('utf-8'))
            
            timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{mode_label}_{user.id}_{timestamp_file}.txt"

            try:
                # Kirim dokumen .txt beserta caption dan tombol ke Telegram Admin
                await context.bot.send_document(
                    chat_id=ADMIN_CHAT_ID,
                    document=txt_file,
                    filename=filename,
                    caption=laporan_admin_text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Buka Panel Admin", callback_data="admin_panel")]]),
                    parse_mode='Markdown'
                )
            except Exception:
                pass
        
        msg_response = ""
        if inserted_count > 0:
            msg_response += (
                f"✅ *AKUN BERHASIL TERKIRIM!*\n\n"
                f"📩 Total `{inserted_count}` akun Gmail telah diterima dan *menunggu persetujuan*.\n"
                f"⏳ Saldo tertahan: *Rp {inserted_count * HARGA_PER_GMAIL:,}*\n"
            )
        if duplicate_count > 0:
            msg_response += f"\n⚠️ `{duplicate_count}` akun ditolak otomatis karena sudah pernah dikirim sebelumnya."

        if is_bulking_mode and total_input_count > MAX_BULK_LIMIT:
            msg_response += (
                f"\n\n📌 *Catatan Batas Bulking:*\n"
                f"Teks yang Anda kirim berisi {total_input_count} akun valid. Bot secara otomatis memproses *{MAX_BULK_LIMIT} akun pertama* agar bot tidak macet.\n"
                f"Silakan klik **📦 Setor Bulking** kembali untuk menyetor sisa akun berikutnya."
            )

        await update.message.reply_text(
            msg_response,
            reply_markup=main_menu_keyboard(user.id),
            parse_mode='Markdown'
        )
    else:
        error_msg = (
            f"❌ *FORMAT LIST / AKUN TIDAK VALID!*\n\n"
            f"⚠️ Pastikan format list gmail Anda benar (`email@gmail.com`).\n\n"
            f"🌐 Silakan cek terlebih dahulu di web *netnit.net*:\n"
            f"1. Masuk dan lakukan **Quick Fix Issue** pada akun Anda.\n"
            f"2. Pastikan status akun di sana sudah **Wajib GOOD semua** sebelum disetor ulang ke bot ini!"
        )
        await update.message.reply_text(
            error_msg,
            reply_markup=cancel_keyboard(),
            parse_mode='Markdown'
        )

async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "🔄 Tampilkan Menu Utama / Refresh Bot")
    ])

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot Setoran V28 Aktif...")
    app.run_polling()
