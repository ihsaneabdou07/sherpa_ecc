import os
import pandas as pd
import requests
from src.parametres import PARAMS as P


def telecharger_meteo(lat, lon, annee=2022, nom="dakhla"):
    """Télécharge un profil horaire NASA POWER (gratuit) et le met en cache en CSV."""
    chemin = os.path.join("data", f"meteo_{nom}_{annee}.csv")
    if os.path.exists(chemin):
        return pd.read_csv(chemin, index_col=0, parse_dates=True)

    url = "https://power.larc.nasa.gov/api/temporal/hourly/point"
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,WS50M,T2M",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": f"{annee}0101",
        "end": f"{annee}1231",
        "format": "JSON",
    }
    r = requests.get(url, params=params, timeout=180)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["properties"]["parameter"])
    df.index = pd.to_datetime(df.index, format="%Y%m%d%H")
    df = df.rename(columns={"ALLSKY_SFC_SW_DWN": "ghi", "WS50M": "vent50", "T2M": "temp"})
    df = df.replace(-999, float("nan")).interpolate()
    df.to_csv(chemin)
    return df


def profil_solaire(df, pr=None):
    """Facteur de charge horaire du solaire (0 à 1). pr = performance ratio."""
    pr = P["pr_solaire"] if pr is None else pr
    return (df["ghi"] / 1000 * pr).clip(0, 1)


def profil_eolien(df, hauteur=None, v_in=None, v_nom=None, v_out=None):
    """Facteur de charge horaire de l'éolien (courbe de puissance simplifiée)."""
    hauteur = P["eolien_hauteur"] if hauteur is None else hauteur
    v_in = P["eolien_v_in"] if v_in is None else v_in
    v_nom = P["eolien_v_nom"] if v_nom is None else v_nom
    v_out = P["eolien_v_out"] if v_out is None else v_out
    v = df["vent50"] * (hauteur / 50) ** P["eolien_cisaillement"]
    cf = (((v - v_in) / (v_nom - v_in)) ** 3).clip(0, 1)
    cf[(v < v_in) | (v > v_out)] = 0
    return cf


def profil_hybride(df, part_solaire=None):
    part = P["part_solaire_hybride"] if part_solaire is None else part_solaire
    return part * profil_solaire(df) + (1 - part) * profil_eolien(df)