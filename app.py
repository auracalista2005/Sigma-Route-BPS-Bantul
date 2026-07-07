import streamlit as st
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# --- FUNGSI MATEMATIKA (Wajib Ikut Disalin) ---
def create_distance_matrix(coordinates):
    num_points = len(coordinates)
    distance_matrix = np.zeros((num_points, num_points), dtype=int)
    for i in range(num_points):
        for j in range(num_points):
            if i == j:
                distance_matrix[i][j] = 0
            else:
                dist = geodesic(coordinates[i], coordinates[j]).meters
                distance_matrix[i][j] = int(dist)
    return distance_matrix.tolist()

def solve_vrp(distance_matrix, num_vehicles, depot_index):
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    
    solution = routing.SolveWithParameters(search_parameters)
    routes = []
    if solution:
        for vehicle_id in range(num_vehicles):
            index = routing.Start(vehicle_id)
            route = []
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))
            routes.append(route)
    return routes

def generate_maps_link(route, coordinates):
    base_url = "https://www.google.com/maps/dir/"
    url_parts = []
    for node in route:
        lat, lon = coordinates[node]
        url_parts.append(f"{lat},{lon}")
    return base_url + "/".join(url_parts)

# --- TAMPILAN WEB STREAMLIT ---
st.title("📊 SIGMA-Route BPS")
st.subheader("Aplikasi Optimisasi Rute Survei Lapangan Terpendek")

uploaded_file = st.file_uploader("Pilih File Excel Sampel BPS (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.write("### Preview Data Responden:")
    st.dataframe(df)
    
    jumlah_petugas = st.number_input("Masukkan Jumlah Petugas Lapangan:", min_value=1, value=1, step=1)
    
    if st.button("Hitung Rute Teroptimal 🚀"):
        with st.spinner("Sedang menghitung rute..."):
            coords = df[['Latitude', 'Longitude']].values.tolist()
            nama_titik = df['Nama'].tolist()
            
            dist_matrix = create_distance_matrix(coords)
            hasil_rute = solve_vrp(dist_matrix, int(jumlah_petugas), 0)
            
            st.success("Perhitungan Selesai!")
            st.write("### 📍 Rute Hasil Optimisasi:")
            
            for i, rute in enumerate(hasil_rute):
                st.write(f"#### Rute untuk Petugas {i+1}:")
                urutan_nama = [nama_titik[node] for node in rute]
                st.info(" ➡️ ".join(urutan_nama))
                
                link_maps = generate_maps_link(rute, coords)
                st.markdown(f"[🗺️ Buka Navigasi Google Maps Petugas {i+1}]({link_maps})", unsafe_allow_html=True)