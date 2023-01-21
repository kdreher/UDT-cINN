import numpy as np
import matplotlib.pyplot as plt
import glob
import os
import matplotlib
matplotlib.use('TkAgg')


data_set_1_root = "/home/kris/Work/Data/domain_adaptation_simulations/min_max_preprocessed_data_sqrt_ms/good_simulations/training"
data_set_2_root = "/home/kris/Work/Data/domain_adaptation_simulations/min_max_preprocessed_data_sqrt_ms/real_images/training"
# data_set_3_root = "/home/kris/networkdrives/E130-Projekte/Photoacoustics/Projects/CVPR_2022/Segmentation_Task/noise_reduced/model_images/training"

files_data_set_1 = glob.glob(os.path.join(data_set_1_root, "*.npz"))
files_data_set_2 = glob.glob(os.path.join(data_set_2_root, "*.npz"))
# files_data_set_3 = glob.glob(os.path.join(data_set_3_root, "*.npz"))


def calculate_mean_spectrum(image_files: list, return_std: bool = True, number_of_wavelengths: int = 16,
                            visualize: bool = False):

    artery_spectra_all = list()
    vein_spectra_all = list()

    # artery_oxygenations, vein_oxygenations = list(), list()

    for im_idx, image_file in enumerate(image_files):
        data = np.load(image_file)
        try:
            seg = np.squeeze(data["segmentation"])
        except KeyError as e:
            continue

        ms_image = np.squeeze(data["reconstruction"])
        if im_idx == 0 and visualize:
            plt.subplot(1, 2, 1)
            plt.imshow(seg)
            plt.subplot(1, 2, 2)
            plt.imshow(ms_image[0, :, :])
            plt.show()

        vein_spectra = ms_image[:, seg == 5]
        # vein_oxygenations.extend(oxy[seg == 5].flatten())
        if vein_spectra.size:
            norm = np.linalg.norm(vein_spectra, axis=0)
            vein_spectra /= norm
            # vein_spectra = (vein_spectra - np.min(vein_spectra, axis=0)) / (np.max(vein_spectra, axis=0) - np.min(vein_spectra, axis=0))

            vein_spectra_all.extend([vein_spectra[:, spectrum] for spectrum in range(np.shape(vein_spectra)[1])])

        artery_spectra = ms_image[:, seg == 6]
        # artery_oxygenations.extend(oxy[seg == 6].flatten())
        if artery_spectra.size:
            artery_spectra /= np.linalg.norm(artery_spectra, axis=0)

            # artery_spectra = (artery_spectra - np.min(artery_spectra, axis=0)) / (np.max(artery_spectra, axis=0) - np.min(artery_spectra, axis=0))

            artery_spectra_all.extend([artery_spectra[:, spectrum] for spectrum in range(np.shape(artery_spectra)[1])])

    mean_artery_spectrum = np.mean(np.array(artery_spectra_all), axis=0)
    mean_vein_spectrum = np.mean(np.array(vein_spectra_all), axis=0)

    return_dict = {
        "mean_artery_spectra": mean_artery_spectrum,
        "mean_vein_spectra": mean_vein_spectrum,
    }

    if return_std:
        std_artery_spectrum = np.std(np.array(artery_spectra_all), axis=0)
        std_vein_spectrum = np.std(np.array(vein_spectra_all), axis=0)

        return_dict["std_artery_spectra"] = std_artery_spectrum
        return_dict["std_vein_spectra"] = std_vein_spectrum

    return return_dict


if __name__ == "__main__":
    sim_spectra = calculate_mean_spectrum(files_data_set_1, return_std=True)
    real_spectra = calculate_mean_spectrum(files_data_set_2, return_std=True)

    wavelengths = np.arange(700, 855, 10)
    plt.subplot(2, 1, 1)
    plt.plot(wavelengths, sim_spectra["mean_vein_spectra"], label="sim veins")
    plt.fill_between(wavelengths, sim_spectra["mean_vein_spectra"] - sim_spectra["std_vein_spectra"],
                     sim_spectra["mean_vein_spectra"] + sim_spectra["std_vein_spectra"], alpha=0.3)
    plt.plot(wavelengths, sim_spectra["mean_artery_spectra"], label="sim arteries")
    plt.fill_between(wavelengths, sim_spectra["mean_artery_spectra"] - sim_spectra["std_artery_spectra"],
                     sim_spectra["mean_artery_spectra"] + sim_spectra["std_artery_spectra"], alpha=0.3)
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.plot(wavelengths, real_spectra["mean_vein_spectra"], label="real veins")
    plt.fill_between(wavelengths, real_spectra["mean_vein_spectra"] - real_spectra["std_vein_spectra"],
                     real_spectra["mean_vein_spectra"] + real_spectra["std_vein_spectra"], alpha=0.3)
    plt.plot(wavelengths, real_spectra["mean_artery_spectra"], label="real arteries")
    plt.fill_between(wavelengths, real_spectra["mean_artery_spectra"] - real_spectra["std_artery_spectra"],
                     real_spectra["mean_artery_spectra"] + real_spectra["std_artery_spectra"], alpha=0.3)
    plt.legend()

    # plt.subplot(3, 1, 3)
    # plt.plot(wavelengths, sim2real_spectra["mean_vein_spectra"], label="sim2real veins")
    # plt.fill_between(wavelengths, sim2real_spectra["mean_vein_spectra"] - sim2real_spectra["std_vein_spectra"],
    #                  sim2real_spectra["mean_vein_spectra"] + sim2real_spectra["std_vein_spectra"], alpha=0.3)
    # plt.plot(wavelengths, sim2real_spectra["mean_artery_spectra"], label="sim2real arteries")
    # plt.fill_between(wavelengths, sim2real_spectra["mean_artery_spectra"] - sim2real_spectra["std_artery_spectra"],
    #                  sim2real_spectra["mean_artery_spectra"] + sim2real_spectra["std_artery_spectra"], alpha=0.3)
    # plt.legend()

    plt.legend()
    plt.show()
    plt.close()

    plt.subplot(2, 1, 1)
    plt.title("Artery spectra")

    plt.plot(wavelengths, sim_spectra["mean_artery_spectra"], label="sim arteries")
    plt.fill_between(wavelengths, sim_spectra["mean_artery_spectra"] - sim_spectra["std_artery_spectra"],
                     sim_spectra["mean_artery_spectra"] + sim_spectra["std_artery_spectra"], alpha=0.3)
    plt.plot(wavelengths, real_spectra["mean_artery_spectra"], label="real arteries")
    plt.fill_between(wavelengths, real_spectra["mean_artery_spectra"] - real_spectra["std_artery_spectra"],
                     real_spectra["mean_artery_spectra"] + real_spectra["std_artery_spectra"], alpha=0.3)

    # plt.plot(wavelengths, sim2real_spectra["mean_artery_spectra"], label="sim2real arteries")
    # plt.fill_between(wavelengths, sim2real_spectra["mean_artery_spectra"] - sim2real_spectra["std_artery_spectra"],
    #                  sim2real_spectra["mean_artery_spectra"] + sim2real_spectra["std_artery_spectra"], alpha=0.3)

    plt.legend()

    plt.subplot(2, 1, 2)
    plt.title("Vein spectra")

    plt.plot(wavelengths, sim_spectra["mean_vein_spectra"], label="sim veins")
    plt.fill_between(wavelengths, sim_spectra["mean_vein_spectra"] - sim_spectra["std_vein_spectra"],
                     sim_spectra["mean_vein_spectra"] + sim_spectra["std_vein_spectra"], alpha=0.3)

    plt.plot(wavelengths, real_spectra["mean_vein_spectra"], label="real veins")
    plt.fill_between(wavelengths, real_spectra["mean_vein_spectra"] - real_spectra["std_vein_spectra"],
                     real_spectra["mean_vein_spectra"] + real_spectra["std_vein_spectra"], alpha=0.3)

    # plt.plot(wavelengths, sim2real_spectra["mean_vein_spectra"], label="sim2real veins")
    # plt.fill_between(wavelengths, sim2real_spectra["mean_vein_spectra"] - sim2real_spectra["std_vein_spectra"],
    #                  sim2real_spectra["mean_vein_spectra"] + sim2real_spectra["std_vein_spectra"], alpha=0.3)

    plt.legend()

    plt.show()
    plt.close()
