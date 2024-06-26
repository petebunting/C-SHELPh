#!/usr/bin/env python
# coding: utf-8

"""
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from typing import List
import sys
from cshelph import cshelph

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def run_cshelph(
    input_h5_file: str,
    laser_num: int,
    thresh: int,
    threshlist: List[int],
    output: str,
    lat_res: float,
    h_res: float,
    water_temp: float,
    start_lat: float,
    end_lat: float,
    min_buffer: float,
    max_buffer: float,
    surface_buffer: float,
):
    """
    This function runs a group of functions processes ICESAT2 data and
    creates a bathymetric model.

    To do this, it follows a number of steps in the form of functions, including:
        1. Reading data (ReadATL03())
        2. Orthometrically correcting the dataset (OrthometricCorrection())
        3. pulling down the data segment ID (getAtl03SegID())
        4. Bin the data along latitudinal and height gradients (bin_data())
        5. Calculate sea height (get_sea_height())
        6. Get water temperature (get_water_temp())
        7. Correct bathymetry surface for refraction (RefractionCorrection())
        8. Calculate bathymetry height (get_bath_height())
        9. produce figures (produce_figures())

    :param input_h5_file:
    :param laser_num:
    :param thresh:
    :param threshlist:
    :param output:
    :param lat_res:
    :param h_res:
    :param water_temp:
    :param start_lat:
    :param end_lat:
    :param min_buffer:
    :param max_buffer:
    :param surface_buffer:
    :return:
    """

    # Read in the data
    try:
        (
            latitude,
            longitude,
            photon_h,
            conf,
            ref_elev,
            ref_azimuth,
            ph_index_beg,
            segment_id,
            alt_sc,
            seg_ph_count,
        ) = cshelph.read_atl03(input_h5_file, laser_num)

        # Find the epsg code
        epsg_code = cshelph.convert_wgs_to_utm(latitude[0], longitude[0])
        epsg_num = int(epsg_code.split(":")[-1])

        # Orthometrically correct the data using the epsg code
        lat_utm, lon_utm, photon_h = cshelph.orthometric_correction(
            latitude, longitude, photon_h, epsg_code
        )

        # count number of photons in each segment: DEPRECATED
        # ph_num_per_seg = count_ph_per_seg(ph_index_beg, photon_h)
        ph_num_per_seg = seg_ph_count[ph_index_beg > 0]
        # Cast as an int
        ph_num_per_seg = ph_num_per_seg.astype(np.int64)

        # count_ph_per_seg() function removes zeros from ph_index_beg
        # These 0s are nodata vals in other params (ref_elev etc)
        # Thus no pre-processing is needed as it will map correctly given
        # the nodata values are eliminated
        ph_ref_elev = cshelph.ref_linear_interp(
            ph_num_per_seg, ref_elev[ph_index_beg > 0]
        )
        ph_ref_azimuth = cshelph.ref_linear_interp(
            ph_num_per_seg, ref_azimuth[ph_index_beg > 0]
        )
        ph_sat_alt = cshelph.ref_linear_interp(ph_num_per_seg, alt_sc[ph_index_beg > 0])

        ###########################################################################
        ########### Hacked Solution to Resolving Differences in Length ############
        ###########################################################################
        lat_utm_len = len(lat_utm)
        lon_utm_len = len(lon_utm)
        photon_h_len = len(photon_h)
        conf_len = len(conf)
        if (
            (lat_utm_len != lon_utm_len)
            and (conf_len != lon_utm_len)
            and (conf_len != photon_h_len)
        ):
            raise Exception("lat_utm, lon_utm and conf_len must have same length")

        ph_ref_elev_len = len(ph_ref_elev)
        ph_ref_azimuth_len = len(ph_ref_azimuth)
        ph_sat_alt_len = len(ph_sat_alt)

        if (ph_ref_elev_len != ph_ref_azimuth_len) and (
            ph_ref_azimuth_len != ph_sat_alt_len
        ):
            raise Exception(
                "ph_ref_elev, ph_ref_azimuth and ph_sat_alt must have same length"
            )

        if lat_utm_len != ph_ref_elev_len:
            if ph_ref_elev_len > lat_utm_len:
                ph_ref_elev = ph_ref_elev[0:lat_utm_len]
                ph_ref_azimuth = ph_ref_azimuth[0:lat_utm_len]
                ph_sat_alt = ph_sat_alt[0:lat_utm_len]
            elif lat_utm_len > ph_ref_elev_len:
                lat_utm = lat_utm[0:ph_ref_elev_len]
                lon_utm = lon_utm[0:ph_ref_elev_len]
                photon_h = photon_h[0:ph_ref_elev_len]
                conf = conf[0:ph_ref_elev_len]
            else:
                raise Exception("Interpolated variables do not have same length")
        ###########################################################################
        ###########################################################################

        # Aggregate data into dataframe
        dataset_sea = pd.DataFrame(
            {
                "latitude": lat_utm,
                "longitude": lon_utm,
                "photon_height": photon_h,
                "confidence": conf,
                "ref_elevation": ph_ref_elev,
                "ref_azminuth": ph_ref_azimuth,
                "ref_sat_alt": ph_sat_alt,
            },
            columns=[
                "latitude",
                "longitude",
                "photon_height",
                "confidence",
                "ref_elevation",
                "ref_azminuth",
                "ref_sat_alt",
            ],
        )

        # plt.scatter(lat_utm, photon_h, c='black', s=0.1, alpha=0.1)
        # plt.show()
        # Filter data that should not be analyzed
        # Filter for quality flags
        dataset_sea1 = dataset_sea[
            (dataset_sea.confidence != 0) & (dataset_sea.confidence != 1)
        ]
        # Filter for elevation range
        dataset_sea1 = dataset_sea1[
            (dataset_sea1["photon_height"] > min_buffer)
            & (dataset_sea1["photon_height"] < max_buffer)
        ]

        # Focus on specific latitude
        if start_lat is not None:
            dataset_sea1 = dataset_sea1[
                (dataset_sea1["latitude"] > start_lat)
                & (dataset_sea1["latitude"] < end_lat)
            ]

        # plt.scatter(dataset_sea1['latitude'], dataset_sea1['photon_height'],c='black',s=0.2,alpha=0.1)
        # plt.show()
        # Bin dataset
        print(dataset_sea1.head())
        binned_data_sea = cshelph.bin_data(dataset_sea1, lat_res, h_res)

        # Find mean sea height
        if surface_buffer == -0.5:
            surface_buffer = -0.5
        else:
            surface_buffer = surface_buffer

        sea_height = cshelph.get_sea_height(binned_data_sea, surface_buffer)

        # Set sea height
        med_water_surface_h = np.nanmedian(sea_height)

        # Calculate sea temperature
        if water_temp is None:
            try:
                water_temp = cshelph.get_water_temp(input_h5_file, latitude, longitude)
            except Exception as e:
                print("NO SST PROVIDED OR RETRIEVED: 20 degrees C assigned")
                water_temp = 20

        print("water temp:", water_temp)

        # Correct for refraction
        print("refrac correction")
        ref_x, ref_y, ref_z, ref_conf, raw_x, raw_y, raw_z, ph_ref_azi, ph_ref_elev = (
            cshelph.refraction_correction(
                water_temp,
                med_water_surface_h,
                532,
                dataset_sea1.ref_elevation,
                dataset_sea1.ref_azminuth,
                dataset_sea1.photon_height,
                dataset_sea1.longitude,
                dataset_sea1.latitude,
                dataset_sea1.confidence,
                dataset_sea1.ref_sat_alt,
            )
        )

        # Find bathy depth
        depth = med_water_surface_h - ref_z

        # Create new dataframe with refraction corrected data
        dataset_bath = pd.DataFrame(
            {
                "latitude": raw_y,
                "longitude": raw_x,
                "cor_latitude": ref_y,
                "cor_longitude": ref_x,
                "cor_photon_height": ref_z,
                "photon_height": raw_z,
                "confidence": ref_conf,
                "depth": depth,
            },
            columns=[
                "latitude",
                "longitude",
                "photon_height",
                "cor_latitude",
                "cor_longitude",
                "cor_photon_height",
                "confidence",
                "depth",
            ],
        )

        # Bin dataset again for bathymetry
        binned_data = cshelph.bin_data(dataset_bath, lat_res, h_res)

        print("Locating bathymetric photons...")
        if isinstance(thresh, int):
            # Find bathymetry
            bath_height, geo_df = cshelph.get_bath_height(
                binned_data, thresh, med_water_surface_h, h_res
            )

            # Create figure
            plt.close()
            print("Creating figs and writing to GPKG")
            cshelph.produce_figures(
                binned_data,
                bath_height,
                sea_height,
                10,
                -20,
                thresh,
                input_h5_file,
                geo_df,
                ref_y,
                ref_z,
                laser_num,
                epsg_num,
            )
        elif isinstance(threshlist, list):
            for thresh in threshlist:
                print("using threshold:", str(thresh))
                bath_height, geo_df = cshelph.get_bath_height(
                    binned_data, int(thresh), med_water_surface_h, h_res
                )

                # Create figure
                plt.close()
                print("Creating figs and writing to GPKG")
                cshelph.produce_figures(
                    binned_data,
                    bath_height,
                    sea_height,
                    10,
                    -20,
                    str(thresh),
                    input_h5_file,
                    geo_df,
                    ref_y,
                    ref_z,
                    laser_num,
                    epsg_num,
                )
    except Exception as e:
        raise e
