from scraper import _build_header_index, _column


def test_warga_export_pppoe_columns_follow_headers():
    rows = [
        """
        <tr>
            <th>No</th>
            <th>ID</th>
            <th>Account</th>
            <th>ID Pelanggan</th>
            <th>Tanggal Registrasi</th>
            <th>Nama Pelanggan</th>
            <th>Username Login APK</th>
            <th>Password Login APK</th>
            <th>Email</th>
            <th>Alamat</th>
            <th>Tlp</th>
            <th>Tlp2</th>
            <th>No ID Identitas</th>
            <th>Foto KTP</th>
            <th>ID Langganan</th>
            <th>Nama Langganan</th>
            <th>Keterangan</th>
            <th>Jenis</th>
            <th>Harga</th>
            <th>PPN</th>
            <th>Kode Unik</th>
            <th>Harga + Kode Unik</th>
            <th>Jatuh Tempo</th>
            <th>Pembayaran Terakhir</th>
            <th>Jenis Tagihan</th>
            <th>Tanggal Tagihan</th>
            <th>Tanggal Isolir</th>
            <th>MAC Adress</th>
            <th>IP / Secret</th>
            <th>Password Secret</th>
            <th>Nama Lokasi</th>
            <th>Jenis Koneksi</th>
            <th>Nama Router</th>
            <th>ID Sales</th>
            <th>Nama Sales</th>
            <th>Metode Insentif</th>
            <th>Insentif Sales</th>
            <th>Status Langganan</th>
            <th>Titik Koordinat Lokasi</th>
        </tr>
        """
    ]
    cols = [f"value-{idx}" for idx in range(39)]
    cols[25] = "2026-05-24"
    cols[26] = "2026-05-24"
    cols[28] = "CUSTOMER_SECRET"
    cols[29] = "SECRET_PASSWORD"

    header_index = _build_header_index(rows)

    assert _column(cols, header_index, "IP / Secret", 28) == "CUSTOMER_SECRET"
    assert _column(cols, header_index, "Password Secret", 29) == "SECRET_PASSWORD"

