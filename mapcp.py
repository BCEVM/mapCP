import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
import contextily as ctx
from pyproj import Transformer
import re
import requests

def get_lat_lon_from_link(link):
    """
    Extract koordinat dari berbagai format Google Maps link
    """
    # Untuk link pendek goo.gl, coba resolve dulu
    if 'goo.gl' in link or 'maps.app.goo.gl' in link:
        try:
            print("🔄 Mengurai link pendek...")
            response = requests.get(link, allow_redirects=True)
            link = response.url
            print(f"✅ Link diperluas: {link[:100]}...")
        except Exception as e:
            print(f"❌ Gagal mengurai link: {e}")
    
    # Format 1: ?q=lat,lon
    match = re.search(r'q=([-\d.]+),([-\d.]+)', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    # Format 2: @lat,lon,zoom
    match = re.search(r'@([-\d.]+),([-\d.]+),', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    # Format 3: /maps/place/.../@lat,lon
    match = re.search(r'/maps/place/.*/@([-\d.]+),([-\d.]+)', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    # Format 4: ll=lat,lon
    match = re.search(r'll=([-\d.]+),([-\d.]+)', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    # Format 5: /maps/@lat,lon
    match = re.search(r'/maps/@([-\d.]+),([-\d.]+)', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    # Format 6: /search/lat,+lon atau /search/lat,lon
    match = re.search(r'/search/([-\d.]+),\+?([-\d.]+)', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    # Format 7: /search/lat,%20lon (dengan %20 sebagai spasi)
    match = re.search(r'/search/([-\d.]+),%20([-\d.]+)', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    # Jika tidak ada yang cocok, minta input manual
    print("❌ Tidak bisa extract koordinat dari link tersebut.")
    print("📝 Contoh input yang benar:")
    print("   Latitude: -7.464340")
    print("   Longitude: 112.429017")
    print()
    lat = float(input("Latitude (contoh: -7.464340): "))
    lon = float(input("Longitude (contoh: 112.429017): "))
    return lat, lon

def create_circle(lat, lon, radius_m=250):
    """
    Membuat lingkaran dengan radius tertentu dalam meter
    """
    # Transform ke koordinat meter (Web Mercator)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x_center, y_center = transformer.transform(lon, lat)
    
    # Buat point center dan buffer dengan radius
    center_point = Point(x_center, y_center)
    circle = center_point.buffer(radius_m)
    
    return gpd.GeoDataFrame(index=[0], crs='EPSG:3857', geometry=[circle])

def plot_map(link, kelurahan, kecamatan, kabupaten, provinsi, radius_m=250, output_name="lokasi"):
    lat, lon = get_lat_lon_from_link(link)
    gdf = create_circle(lat, lon, radius_m)

    fig, ax = plt.subplots(figsize=(10, 12))  # Tambah tinggi visualisasi
    gdf.plot(ax=ax, facecolor='red', alpha=0.3, edgecolor='yellow', linewidth=3)

    try:
        ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, zoom=19)
    except Exception as e:
        print("⚠️ Gagal load Esri, fallback ke OpenStreetMap")
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=19)

    x, y = gdf.geometry[0].centroid.x, gdf.geometry[0].centroid.y
    ax.text(x, y,
            f"{kelurahan}\n{kecamatan}\n{kabupaten}\n{provinsi}",
            fontsize=12, color='white', ha='center',
            bbox=dict(facecolor='black', alpha=0.5))

    # Tambahkan identitas pembuat di pojok kiri bawah
    ax.text(
        0.01, 0.01,
        "Tools ini dibuat oleh BCEVM - HACKTIVIST INDONESIA",
        transform=ax.transAxes,
        fontsize=10,
        color='red',
        ha='left',
        va='bottom',
        bbox=dict(facecolor='black', alpha=0.4, pad=4)
    )
    
    plt.axis('off')
    # Hitung luas lingkaran
    area = 3.14159 * (radius_m ** 2)
    plt.title(f"Peta Lokasi - Radius {radius_m}m (Luas ≈{area:.0f}m²)", fontsize=14, color='white')
    plt.tight_layout()
    filename = f"{output_name}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Disimpan sebagai: {filename}")

# ==== INPUT MANUAL ====
if __name__ == "__main__":
    link = input("Paste link Google Maps (format ?q=lat,lon): ").strip()
    kelurahan = input("Kelurahan: ").strip().upper()
    kecamatan = input("Kecamatan: ").strip().upper()
    kabupaten = input("Kab/Kota: ").strip().upper()
    provinsi = input("Provinsi: ").strip().upper()
    radius = int(input("Radius dalam meter (default 250): ").strip() or "250")
    output_name = input("Simpan sebagai nama file (tanpa .png): ").strip()

    plot_map(link, kelurahan, kecamatan, kabupaten, provinsi, radius, output_name)
