#!/usr/bin/env python

import os
import os.path
import subprocess
import multiprocessing as mp
import argparse
import json
from math import radians, log10

debug = False


def executeCmd(cmd):
    print("Running", cmd)
    if not debug:
        return subprocess.run([cmd], shell=True)


class JobProcessor:
    def __init__(self, script, outdir, output_tag):
        self.script = script
        self.outdir = outdir
        self.output_tag = output_tag
        self.extra_args = ""
        os.makedirs(outdir, exist_ok=True)

    def process(self, nevt, energy, theta, jobId):
        thetarad = radians(theta)
        cmd = f"fccrun {self.script} -n {nevt} --MomentumMin {energy} --MomentumMax {energy} --ThetaMin {thetarad} --ThetaMax {thetarad}\
            --filename {self.outdir}/{self.output_tag}_energy_{energy}_theta_{theta}_jobid_{jobId}.root --seedValue {jobId} {self.extra_args}"
        return executeCmd(cmd)

    def hadd(self, energy, theta):
        filestub = f"{self.outdir}/{self.output_tag}_energy_{energy}_theta_{theta}"
        cmd = f"hadd -f {filestub}.root {filestub}_jobid_*.root"
        return executeCmd(cmd)

    def rm(self, energy, theta):
        cmd = f"rm -f {self.outdir}/{self.output_tag}_energy_{energy}_theta_{theta}_jobid_*.root"
        return executeCmd(cmd)


class SamplingJobProcessor(JobProcessor):
    def __init__(self, outdir):
        script = "fcc_ee_samplingFraction_inclinedEcal.py"
        output_tag = "sampling_output"
        super().__init__(script, outdir, output_tag)

    def process(self, nevt, energy, theta, jobId):
        thetarad = radians(theta)
        cmd = f"""fccrun {self.script} -n {nevt} --MomentumMin {energy} --MomentumMax {energy} --ThetaMin {thetarad} --ThetaMax {thetarad}\
            --Output.THistSvc "rec DATAFILE='{self.outdir}/calibration_{self.output_tag}_energy_{energy}_theta_{theta}_jobid_{jobId}.root' TYP='ROOT' OPT='RECREATE'" \
            --filename {self.outdir}/{self.output_tag}_energy_{energy}_theta_{theta}_jobid_{jobId}.root --seedValue {jobId} {self.extra_args}"""
        return executeCmd(cmd)

    def hadd(self, energy, theta):
        filestub = f"{self.outdir}/{self.output_tag}_energy_{energy}_theta_{theta}"
        cmd = f"hadd -f {filestub}.root {filestub}_jobid_*.root"
        executeCmd(cmd)
        filestub = f"{self.outdir}/calibration_{self.output_tag}_energy_{energy}_theta_{theta}"
        cmd = f"hadd -f {filestub}.root {filestub}_jobid_*.root"
        return executeCmd(cmd)

    def rm(self, energy, theta):
        subprocess.run([f"rm -f {self.outdir}/{self.output_tag}_energy_{energy}_theta_{theta}_jobid_*.root"], shell=True)
        cmd = f"rm -f {self.outdir}/calibration_{self.output_tag}_energy_{energy}_theta_{theta}_jobid_*.root"
        return executeCmd(cmd)

    def postprocess(self, energy, theta):
        # make plots of sampling fraction, save SFs to json, and update the values in the python scripts
        energy_GeV = int(energy / 1.e3)
        cmd = f"python FCC_calo_analysis_cpp/plot_samplingFraction.py \
            {self.outdir}/calibration_{self.output_tag}_energy_{energy}_theta_{theta}.root {energy_GeV} \
            --preview -outputfolder {self.outdir} --json {self.outdir}/SF.json --sed"
        return executeCmd(cmd)

    def postprocess_glob(self):
        return 0


class UpstreamJobProcessor(JobProcessor):
    def __init__(self, outdir, sampling_fracs=None, postprocess_scripts_dir=None):
        script = "fcc_ee_upstream_inclinedEcal.py"
        output_tag = "upstream_output"
        super().__init__(script, outdir, output_tag)
        if sampling_fracs:
            self.extra_args += "--samplingFractions "
            self.extra_args += ' '.join([str(s) for s in sampling_fracs])
            self.extra_args += ' '
        self.postprocess_dir = os.path.join(os.getenv("FCCBASEDIR"), 'k4SimGeant4/Detector/DetStudies/scripts/')

    def postprocess(self, energy, theta):
        # for each energy point, determine (fit) the dependence of energy upstream vs energy in 1st layer
        emax = 0.015 * (1. + log10(energy / 1000.))
        emin = 0.002 * (1. + log10(energy / 1000.))
        cmd = f"{self.postprocess_dir}/cec_process_events -i {self.outdir}/{self.output_tag}_energy_{energy}_theta_{theta}.root -t upstream --plot-file-format png \
            -o {self.outdir}/fit_results.json --plot-directory {self.outdir} --func-from {emin} --func-to {emax}"
        executeCmd(cmd)

        # for each energy point, determine (fit) the dependence of energy downstream vs energy in last layer
        emax = 0.04 * energy / 1000
        if energy >= 10000:
            emax *= (log10(energy / 1000.))
        emin = 0.005
        cmd = f"{self.postprocess_dir}/cec_process_events -i {self.outdir}/{self.output_tag}_energy_{energy}_theta_{theta}.root -t downstream --function pol2  \
        --plot-file-format png -o {self.outdir}/fit_results.json --plot-directory {self.outdir}  --func-from {emin} --func-to {emax}"
        return executeCmd(cmd)

    def postprocess_glob(self):
        # fit the dependence of the coefficients of the upstream corrections on energy and save to json
        cmd = f"{self.postprocess_dir}/cec_derive1 -i {self.outdir}/fit_results.json -t upstream --plot-file-format png \
            --plot-directory {self.outdir} --functions '[0]+[1]/(x-[2])' '[0]+[1]/(x-[2])'"
        executeCmd(cmd)

        # fit the dependence of the coefficients of the downsstream corrections on energy and save to json
        cmd = f"{self.postprocess_dir}/cec_derive1 -i {self.outdir}/fit_results.json -t downstream --plot-file-format png \
            --plot-directory {self.outdir} --functions '[0]+[1]*x' '[0]+[1]/sqrt(x)' '[0]+[1]/x'"
        executeCmd(cmd)

        # update the values of the parameters in the python scripts
        cmd = f"python read_upstream_json.py {self.outdir}/corr_params_1d.json"
        return executeCmd(cmd)


class ClusterJobProcessor(JobProcessor):
    def __init__(self, outdir, sampling_fracs=None, corrections=None):
        # script = "runTopoAndSlidingWindowAndCaloSim.py"
        script = "run_thetamodulemerged.py"
        output_tag = "cluster_output"
        super().__init__(script, outdir, output_tag)
        if sampling_fracs:
            self.extra_args += "--samplingFraction "
            self.extra_args += ' '.join([str(s) for s in sampling_fracs])
            self.extra_args += ' '
        self.corrections = corrections

    def preprocess(self):
        if self.corrections:
            upstream_str = ', '.join([str(s) for s in self.corrections['up']])
            downstream_str = ', '.join([str(s) for s in self.corrections['do']])
            cmd = f"sed -i 's/upstreamParameters =.*,/upstreamParameters = [[{upstream_str}]],/' {self.script}"
            executeCmd(cmd)
            cmd = f"sed -i 's/downstreamParameters =.*,/downstreamParameters = [[{downstream_str}]],/' {self.script}"
            executeCmd(cmd)
            cmd = f"sed -i 's/saveHits *=.*/saveHits = False/' {self.script}"
            executeCmd(cmd)
            cmd = f"sed -i 's/saveCells *=.*/saveCells = False/' {self.script}"
            return executeCmd(cmd)


class ProductionJobProcessor(JobProcessor):
    def __init__(self, script, outdir, output_tag):
        super().__init__(script, outdir, output_tag)

    def process(self, nevt, jobId):
        cmd = f"fccrun {self.script} -n {nevt} --MomentumMin 200 --MomentumMax 120000 \
            --filename {self.outdir}/{self.output_tag}_jobid_{jobId}.root --seedValue {jobId} {self.extra_args}"
        print("Running", cmd)
        if not debug:
            return subprocess.run([cmd], shell=True)

    def hadd(self):
        filestub = f"{self.outdir}/{self.output_tag}"
        cmd = f"hadd -f {filestub}.root {filestub}_jobid_*.root"
        print("Running", cmd)
        if not debug:
            return subprocess.run([cmd], shell=True)

    def rm(self):
        cmd = f"rm -f {self.outdir}/{self.output_tag}_jobid_*.root"
        print("Running", cmd)
        if not debug:
            return subprocess.run([cmd], shell=True)


class ClusterProductionJobProcessor(ProductionJobProcessor):
    def __init__(self, outdir, sampling_fracs=None, corrections=None):
        # script = "runTopoAndSlidingWindowAndCaloSim.py"
        script = "run_thetamodulemerged.py"
        output_tag = "cluster_output"
        super().__init__(script, outdir, output_tag)
        if sampling_fracs:
            self.extra_args += "--samplingFraction "
            self.extra_args += ' '.join([str(s) for s in sampling_fracs])
            self.extra_args += ' '
        self.corrections = corrections

    def preprocess(self):
        if self.corrections:
            upstream_str = ', '.join([str(s) for s in self.corrections['up']])
            downstream_str = ', '.join([str(s) for s in self.corrections['do']])
            command = f"sed -i 's/upstreamParameters *=.*,/upstreamParameters = [[{upstream_str}]],/' {self.script}"
            print("Running", command)
            if not debug:
                subprocess.run([command], shell=True)
            command = f"sed -i 's/downstreamParameters *=.*,/downstreamParameters = [[{downstream_str}]],/' {self.script}"
            print("Running", command)
            if not debug:
                subprocess.run([command], shell=True)


class UpstreamProductionJobProcessor(ProductionJobProcessor):
    def __init__(self, outdir, sampling_fracs=None):
        script = "fcc_ee_upstream_with_clusters.py"
        output_tag = "upstream_output"
        super().__init__(script, outdir, output_tag)
        if sampling_fracs:
            self.extra_args += "--samplingFraction.CreateCaloCellsBarrel.CalibrateECalBarrel "
            self.extra_args += ' '.join([str(s) for s in sampling_fracs])
            self.extra_args += ' '


def run_the_jobs(jobProcessor, energies, thetas, nEvt, do_preprocess, do_process, do_postprocess):
    if do_preprocess:
        print("Doing preprocessing")
        jobProcessor.preprocess()

    with mp.Pool() as p:
        nEvtMaxPerJob = [int(1000 * (10000. / e)**1.5) for e in energies]  # 3000 evts for 10GeV, with power scaling
        nEvtPerJob = [min(nEvt, nMax) for nMax in nEvtMaxPerJob]
        args = []
        energies_and_thetas = []
        jobId = 1
        for theta in thetas:
            for e, nEvtPerJobForE in zip(energies, nEvtPerJob):
                nEvtToLaunch = nEvt
                while nEvtToLaunch > 0:
                    nLaunched = min(nEvtToLaunch, nEvtPerJobForE)
                    args.append((nLaunched, e, theta, jobId))
                    jobId += 1
                    nEvtToLaunch -= nLaunched
            for e in energies:
                energies_and_thetas.append((e, theta))

        if do_process:
            print("About to send jobs with parameters:")
            for a in args:
                print(a)
            res = p.starmap_async(jobProcessor.process, args)
            print("Retcodes of the jobs:")
            print(res.get())
            print()

            print("Hadd'ing results:")
            res = p.starmap_async(jobProcessor.hadd, energies_and_thetas)
            print("Retcodes of the jobs:")
            print(res.get())
            print()

            print("Removing intermediate files:")
            res = p.starmap_async(jobProcessor.rm, energies_and_thetas)
            print("Retcodes of the jobs:")
            print(res.get())
            print()

        if do_postprocess:
            print("Doing postprocessing")
            # Do it sequentially
            res = p.starmap(jobProcessor.postprocess, energies_and_thetas, chunksize=50)
            jobProcessor.postprocess_glob()


def run_production(jobProcessor, nEvt, do_preprocess, do_process):
    if do_preprocess:
        print("Doing preprocessing")
        jobProcessor.preprocess()

    with mp.Pool() as p:
        if do_process:
            nEvtMaxPerJob = 300
            nEvtPerJob = min(nEvt, nEvtMaxPerJob)
            args = []
            jobId = 1
            nEvtToLaunch = nEvt
            while nEvtToLaunch > 0:
                nLaunched = min(nEvtToLaunch, nEvtPerJob)
                args.append((nLaunched, jobId))
                jobId += 1
                nEvtToLaunch -= nLaunched

            print("About to send jobs with parameters:")
            for a in args:
                print(a)
            res = p.starmap_async(jobProcessor.process, args)
            print("Retcodes of the jobs:")
            print(res.get())
            print()

            print("Hadd'ing results:")
            jobProcessor.hadd()

            print("Removing intermediate files:")
            jobProcessor.rm()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outDir', default='./', type=str, help='output directory for plots')
    parser.add_argument('--nEvt', default=1000, type=int, help='number of events to process per point')
    parser.add_argument('--energies', default=[], action='extend', nargs='*', type=int,
                        help='energies to process')
    parser.add_argument('--thetas', default=[90], action='extend', nargs='*', type=int,
                        help='thetas (in degrees) to process')
    parser.add_argument('--process', default=True, action=argparse.BooleanOptionalAction, help='if no-process is set, do only the pre- and post-processing - no simulation jobs are run')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--sampling', action='store_true', help='compute the sampling fractions')
    group.add_argument('--upstream', action='store_true', help='compute the upstream corrections')
    group.add_argument('--clusters', action='store_true', help='run fixed size and topo clusterings')
    group.add_argument('--production', action='store_true', help='production run of clusters of all energies')
    group.add_argument('--upstreamProd', action='store_true', help='production run of all energies for upstream')
    parser.add_argument('--SF', default='', type=str, help='JSON file containing sampling fractions')
    parser.add_argument('--corrections', default='', type=str, help='JSON file containing upstream and downstream corrections')
    args = parser.parse_args()

    # remove possible duplicates
    energies = list(set(args.energies))
    thetas = list(set(args.thetas))

    sampling_fracs = None
    if args.SF!="":
        with open(args.SF, 'r') as jsonfile:
            sampling_fracs = json.load(jsonfile)
            print("Applying sampling fractions:", sampling_fracs)

    corrections = None
    if args.corrections!="":
        with open(args.corrections, 'r') as jsonfile:
            source = json.load(jsonfile)
            dict_up = {e['name']: e['value'] for e in source['corr_params'] if e['type'] == 'upstream'}
            dict_do = {e['name']: e['value'] for e in source['corr_params'] if e['type'] == 'downstream'}
            corrections = {}
            corrections['up'] = [dict_up['a'], dict_up['b'], dict_up['c'], dict_up['d'], dict_up['e'], dict_up['f']]
            corrections['do'] = [dict_do['a'], dict_do['b'], dict_do['c'], dict_do['d'], dict_do['e'], dict_do['f']]
            print("Applying up/downstream corrections")
            print(corrections)

    # energies = [500, 1000, 5000, 10000, 15000, 20000, 30000, 50000, 75000, 100000]
    if args.sampling:
        samJobPr = SamplingJobProcessor(args.outDir)
        run_the_jobs(samJobPr, energies, thetas, args.nEvt, False, True and args.process, True)
    if args.upstream:
        upJobPr = UpstreamJobProcessor(args.outDir, sampling_fracs=sampling_fracs)
        run_the_jobs(upJobPr, energies, thetas, args.nEvt, False, True and args.process, True)
    elif args.clusters:
        clJobPr = ClusterJobProcessor(args.outDir, sampling_fracs=sampling_fracs, corrections=corrections)
        run_the_jobs(clJobPr, energies, thetas, args.nEvt, True, True and args.process, False)
    elif args.production:
        clJobPr = ClusterProductionJobProcessor(args.outDir, sampling_fracs=sampling_fracs, corrections=corrections)
        run_production(clJobPr, args.nEvt, True, True and args.process)
    elif args.upstreamProd:
        upJobPr = UpstreamProductionJobProcessor(args.outDir, sampling_fracs=sampling_fracs)
        run_production(upJobPr, args.nEvt, False, True and args.process)


if __name__ == "__main__":
    main()
