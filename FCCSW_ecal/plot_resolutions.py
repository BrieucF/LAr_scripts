#!/usr/bin/env python

import argparse
import os
import os.path
import numpy as np
from matplotlib import pyplot as plt
from scipy import optimize as opt

import ROOT

graphicFormat = 'pdf'

# Define marker styles globally
marker_styles = ['o', '^', 's', 'D', '*', 'x', '|', '+']


def main():
    # enable if seaborn is installed
    #  from matplotlib import style
    # style.use('seaborn-colorblind')

    parser = argparse.ArgumentParser()
    parser.add_argument('--outDir', default='./', type=str, help='output directory for plots')
    parser.add_argument('--doFits', action='store_true', help='Perform resolution fits')
    subparsers = parser.add_subparsers(help='subcommands help')

    parser_p = subparsers.add_parser('plot', help='create simple plots')
    parser_p.set_defaults(func=plot)
    parser_p.add_argument('inputFile', type=str, help='input CSV file')
    parser_p.add_argument('--fileDescr', type=str, help='one-word description of the file (e.g geometry)')
    parser_p.add_argument('--all', action='store_true', help='make all possible plots')
    parser_p.add_argument('--clusters', nargs='+', type=str, help='cluster collections to plot')
    parser_p.add_argument('--distributions', nargs='+', type=str, help='distributions to plot')

    parser_c = subparsers.add_parser('compare', help='compare curves on same figure')
    subparsers_c = parser_c.add_subparsers(help='what to compare')
    parser_f = subparsers_c.add_parser('files', help='compare same distribution in different files')
    parser_f.set_defaults(func=compare_files)
    parser_f.add_argument('inputFile1', type=str, help='first input CSV file')
    parser_f.add_argument('inputFiles', nargs='+', type=str, help='other input CSV files')
    parser_f.add_argument('-d', '--filesDescr', nargs='*', type=str, help='one-word description of each file (e.g geometry)')
    parser_f.add_argument('--all', action='store_true', help='make all possible plots')
    parser_f.add_argument('--clusters', nargs='+', type=str, help='cluster collections to plot')
    parser_f.add_argument('--distributions', nargs='+', type=str, help='distributions to plot')

    parser_cl = subparsers_c.add_parser('clusters', help='compare same distribution for different cluster types')
    parser_cl.set_defaults(func=compare_clusters)
    parser_cl.add_argument('cluster1', type=str, help='first cluster collection to compare')
    parser_cl.add_argument('clusters', nargs='+', type=str, help='other cluster collections to compare')
    parser_cl.add_argument('inputFile', type=str, help='input CSV file')
    parser_cl.add_argument('--fileDescr', type=str, help='one-word description of the file (e.g geometry)')
    parser_cl_g = parser_cl.add_mutually_exclusive_group(required=True)
    parser_cl_g.add_argument('--all', action='store_true', help='make all possible plots')
    parser_cl_g.add_argument('--distributions', nargs='+', type=str, help='distributions to plot')

    args = parser.parse_args()
    os.makedirs(args.outDir, exist_ok=True)
    args.func(args)

def plot(args):
    df = ROOT.RDF.FromCSV(args.inputFile)
    df = add_uncertainties(df)

    if args.all:
        clusters_colls = set([str(cl) for cl in df.AsNumpy(["ClusterType"])["ClusterType"].astype(ROOT.std.string)])
        distributions = all_distributions()
    else:
        clusters_colls = args.clusters
        distributions = args.distributions

    for cl in clusters_colls:
        for d in distributions:
            fig = simple_plot(df, d, cl, do_fit=args.doFits, tag=args.fileDescr)
            if args.fileDescr:
                out_f_name = f"{args.outDir}/fig_{args.fileDescr}_{cl}_{d}.{graphicFormat}"
            else:
                out_f_name = f"{args.outDir}/fig_{cl}_{d}.{graphicFormat}"
            print(f"Saving {out_f_name}")
            fig.savefig(out_f_name)
            plt.close()


def compare_clusters(args):
    df = ROOT.RDF.FromCSV(args.inputFile)
    df = add_uncertainties(df)

    clusters_colls = [args.cluster1] + args.clusters

    if args.all:
        distributions = all_distributions()
    else:
        distributions = args.distributions

    for d in distributions:
        fig = comparison_plot_clusters(df, d, clusters_colls, do_fit=args.doFits, tag=args.fileDescr)
        if args.fileDescr:
            out_f_name = f"{args.outDir}/fig_compare_clusters_{args.fileDescr}_{d}.{graphicFormat}"
        else:
            out_f_name = f"{args.outDir}/fig_compare_clusters_{d}.{graphicFormat}"
        print(f"Saving {out_f_name}")
        fig.savefig(out_f_name)
        plt.close()


def compare_files(args):
    all_files = [args.inputFile1] + args.inputFiles
    if args.filesDescr:
        if len(args.filesDescr) != len(all_files):
            print("ERROR: {0} descriptions provided for {1} files !".format(len(args.filesDescr), len(all_files)))
            return
        tags = args.filesDescr
    else:
        tags = [os.path.splitext(os.path.basename(f))[0] for f in all_files]

    dfs = [add_uncertainties(ROOT.RDF.FromCSV(f)) for f in all_files]

    if args.all:
        clusters_colls = set([str(cl) for cl in dfs[0].AsNumpy(["ClusterType"])["ClusterType"].astype(ROOT.std.string)])
        distributions = all_distributions()
    else:
        clusters_colls = args.clusters
        distributions = args.distributions

    for cl in clusters_colls:
        for d in distributions:
            fig = comparison_plot_files(dfs, tags, d, cl, do_fit=args.doFits)
            out_f_name = f"{args.outDir}/fig_compare_files_{cl}_{d}.{graphicFormat}"
            print(f"Saving {out_f_name}")
            fig.savefig(out_f_name)
            plt.close()
    pass


def add_uncertainties(df):
    resp_columns = ["E_response", "Phi_response", "Theta_response"]
    resol_columns = ["E_resol", "Phi_resol", "Theta_resol"]
    for resp, resol in zip(resp_columns, resol_columns):
        df = df.Define(f"{resp}_err", f"{resol}/sqrt(NeventsPass)")
        df = df.Define(f"{resol}_err", f"{resol}/sqrt(2*NeventsPass - 2)")
    return df


def resol_curve(x, a, b, c):
    return np.sqrt(c * c + b * b / x + a * a / (x * x))


def extract_values(df, name, clusters, do_fit=False, fit_fcn=resol_curve):
    cols = df.Filter(f'ClusterType == "{clusters}"').AsNumpy(["E_truth", name, f"{name}_err"])
    if 'E' in name:
        # Put in % for energy resol
        cols[name] *= 100
        cols[f"{name}_err"] *= 100
    else:
        # Put in mrad for angles
        cols[name] *= 1000
        cols[f"{name}_err"] *= 1000
    popt = None
    if do_fit:
        popt, pcov = opt.curve_fit(fit_fcn, cols["E_truth"], cols[name], sigma=cols[f"{name}_err"], p0=(0, 10, 1))
    return cols["E_truth"], cols[name], cols[f"{name}_err"], popt


def prepare_fig(name, tag=None):
    fig, ax = plt.subplots(figsize=(4.8, 4.8), constrained_layout=True, subplot_kw=dict(box_aspect=1))
    ax.set_xlabel("E (GeV)")
    # ax.set_yscale('log')
    # ax.set_xscale('log')
    if "resp" in name:
        what = "Response"
    elif "resol" in name:
        what = "Resolution"
    if 'E' in name:
        var = "Energy"
    elif 'Phi' in name:
        var = r'$\phi$'
    elif 'Theta' in name:
        var = r'$\theta$'
    if 'E' in name:
        ax.set_ylabel(f"{what} (%)")
    else:
        ax.set_ylabel(f"{what} (mrad)")
    if tag:
        ax.set_title(f"{var} {what} {tag}")
    else:
        ax.set_title(f"{var} {what}")
    return fig, ax


def postprocess_fig(fig, ax, name, leg_entries):
    if "resol" in name:
        ax.set_ylim(ymin=0)
    ax.set_xlim(xmin=0)
    # loc = 'lower right' if "response" in name else 'upper right'
    loc = 'best'
    ax.legend(handles=leg_entries, loc=loc)


def plot_fit(ax, energies, popts, color=None):
    xvals_curve = np.linspace(energies.min(), energies.max(), 200)
    curve, = ax.plot(xvals_curve, resol_curve(xvals_curve, *popts),
                     linestyle='-', color=color,
                     label="$\\frac{{{0:.2f}}}{{E}}\\oplus \\frac{{{1:.1f}\\%}}{{\\sqrt{{E}}}}\\oplus {2:.1f}\\%$".format(popts[0] * 0.01, popts[1], popts[2]))
    return curve


def simple_plot(df, name, clusters, do_fit=False, tag=None):
    if "resol" not in name:
        do_fit = False
    energies, yvals, yvals_err, popts = extract_values(df, name, clusters, do_fit)
    fig, ax = prepare_fig(name, tag)
    marker_style = marker_styles[0]
    leg_entries = [ax.errorbar(energies, yvals, yerr=yvals_err, label=f"{name}, {clusters}", marker=marker_style,
                               linestyle='none')]
    if do_fit:
        leg_entries.append(plot_fit(ax, energies, popts))
    postprocess_fig(fig, ax, name, leg_entries)
    return fig


def comparison_plot_clusters(df, name, clusters, do_fit=False, tag=None):
    if "resol" not in name:
        do_fit = False
    fig, ax = prepare_fig(name, tag)
    leg_entries = []
    for idx, cl in enumerate(clusters):
        energies, yvals, yvals_err, popts = extract_values(df, name, cl, do_fit)
        marker_style = marker_styles[idx % len(marker_styles)] 
        errbar = ax.errorbar(energies, yvals, yerr=yvals_err, label=f"{name}, {cl}", marker=marker_style, linestyle='none')
        leg_entries.append(errbar)
        if do_fit:
            leg_entries.append(plot_fit(ax, energies, popts, color=errbar[0].get_color()))
    postprocess_fig(fig, ax, name, leg_entries)
    return fig


def comparison_plot_files(dfs, tags, name, clusters, do_fit=False):
    if "resol" not in name:
        do_fit = False
    fig, ax = prepare_fig(name, clusters)
    leg_entries = []
    for idx, (df, tag) in enumerate(zip(dfs, tags)):
        energies, yvals, yvals_err, popts = extract_values(df, name, clusters, do_fit)
        marker_style = marker_styles[idx % len(marker_styles)] 
        errbar = ax.errorbar(energies, yvals, yerr=yvals_err, label=f"{tag}", marker=marker_style, linestyle='none')
        leg_entries.append(errbar)
        if do_fit:
            leg_entries.append(plot_fit(ax, energies, popts, color=errbar[0].get_color()))
    postprocess_fig(fig, ax, name, leg_entries)
    return fig


def all_distributions():
    variables = ["E", "Phi", "Theta"]
    var_types = ["resol", "response"]
    distributions = [f"{v}_{t}" for v in variables for t in var_types]
    return distributions


if __name__ == "__main__":
    main()
