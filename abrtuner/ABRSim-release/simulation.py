# SIMULATION 1.0
import math, sys, collections
from config import *
from helpers import *
from chunkMap import *
from performance_vector import *
from algorithms import *
from simulation_performance_vector import *
import numpy as np
import collections
from collections import deque
import time
from vplayer_state import State
import config
import warnings
warnings.filterwarnings('error')

if TRACE_MODE:
    trace_file = sys.argv[1]

for initialBSM in [0.25]:
  gp = getBolaGP()
  bola_vp = getBolaVP(gp)
  for bola_gp in np.arange(gp - 1.5,gp ,0.1):

    s = State(config, trace_file)

    while s.CLOCK < s.sessiontimems:
        play_stalled_this_interval = 0
        chunk_downloaded_this_interval = 0
        blen_added_this_interval = 0
    
        if DEBUG and not s.session_fully_downloaded:
            s.PrintStats()
    
        if s.CLOCK + s.interval > s.sessiontimems:
            s.interval = s.sessiontimems - s.CLOCK
    
        s.chunk_sched_time_delay = max(0, s.chunk_sched_time_delay - s.interval)
    
        s.CLOCK += s.interval
    
        if s.BLEN > s.min_playable_buff:
            s.buffering = False
    
        if s.buffering and not s.session_fully_downloaded:
            play_stalled_this_interval = min(timeToDownloadSingleChunk(CHUNKSIZE, s.BR, s.BW, s.chunk_residue, s.CHUNKS_DOWNLOADED), s.interval / 1000.0)
            if play_stalled_this_interval < s.interval / 1000.0:  # chunk download so resume
                s.buffering = False
        if not s.session_fully_downloaded and s.chunk_sched_time_delay < s.interval:
            s, bola_gp = chunksDownloaded(s, bola_gp, s.CLOCK - s.interval)
            chunk_downloaded_this_interval = s.chunk_residue + s.numChunks
    
            if play_stalled_this_interval == s.interval / 1000.0 and chunk_downloaded_this_interval >= 1.0:
                s.buffering = False

            #old_chunk_residue = s.chunk_residue 
            s.chunk_residue = chunk_downloaded_this_interval - int(chunk_downloaded_this_interval)
            if s.BLEN + chunk_downloaded_this_interval * s.CHUNKSIZE >= MAX_BUFFLEN:  # can't download more than the MAX_BUFFLEN
                chunk_downloaded_this_interval = int(MAX_BUFFLEN - s.BLEN) / CHUNKSIZE
                s.chunk_residue = 0

        if s.CHUNKS_DOWNLOADED + int(chunk_downloaded_this_interval) >= math.ceil((s.playtimems) / (CHUNKSIZE * 1000.0)):
            chunk_downloaded_this_interval = math.ceil((s.playtimems) / (CHUNKSIZE * 1000.0)) - s.CHUNKS_DOWNLOADED
    
        s.clock_inc = s.CLOCK - s.last_clock_val
        s.last_clock_val = s.CLOCK
        if s.numChunks > 0:
           s.realBR = getRealBitrate(s.BR, s.CHUNKS_DOWNLOADED, CHUNKSIZE) / (CHUNKSIZE * 1000.0)
           if chunk_downloaded_this_interval != 0 and s.numChunks > 0 and int(chunk_downloaded_this_interval) != 1 and s.last_chd_interval != 0 and s.last_chd_interval < chunk_downloaded_this_interval:
             s.q.append((s.realBR * CHUNKSIZE * s.numChunks) / (s.clock_inc / 1000.0))
             if s.CLOCK % 100 == 0:
               s.playerVisibleBW.append(np.mean(s.q))
        s.last_chd_interval = chunk_downloaded_this_interval

        #s.CHUNKS_DOWNLOADED_old = s.CHUNKS_DOWNLOADED
        s.CHUNKS_DOWNLOADED += int(chunk_downloaded_this_interval)
        s.ATTEMPT_ID += int(chunk_downloaded_this_interval)
        blen_added_this_interval = int(chunk_downloaded_this_interval) * CHUNKSIZE
    
        if not s.buffering and s.BLEN - s.min_playable_buff >= 0 and s.BLEN - s.min_playable_buff + blen_added_this_interval < s.interval / 1000.0 and not s.session_fully_downloaded:
            play_stalled_this_interval += (s.interval / 1000.0 - (float(s.BLEN) - s.min_playable_buff + float(blen_added_this_interval)) )
            s.buffering = True
    
        if not s.first_chunk and play_stalled_this_interval > 0:
          s.firstRebuf = True
        if not s.first_chunk: 
          s.BUFFTIME += float(play_stalled_this_interval)
          s.PLAYTIME += s.interval / 1000.0 - play_stalled_this_interval

        if s.first_chunk and s.CHUNKS_DOWNLOADED >= 1:
            s.first_chunk = False
    
        if int(chunk_downloaded_this_interval) >= 1:
            s.lastBlen_decisioncycle.append(s.BLEN)
    
        #s.lastBlen = s.BLEN
        if s.buffering:
            s.BLEN = s.min_playable_buff
        elif not s.buffering and s.first_chunk and s.CHUNKS_DOWNLOADED == 0:
            s.BLEN = max(0, float(s.BLEN) - s.interval / 1000.0)
        else:
            s.BLEN = max(0, float(s.CHUNKS_DOWNLOADED) * float(s.CHUNKSIZE) - float(s.PLAYTIME))  # else update the bufferlen to take into account the current time step
    
        if s.CHUNKS_DOWNLOADED >= TOTAL_CHUNKS or s.CHUNKS_DOWNLOADED >= math.ceil((s.playtimems) / (s.CHUNKSIZE * 1000.0)):
            s.session_fully_downloaded = True
            break
    
        if not s.first_chunk and not s.session_fully_downloaded and s.oldBR != s.BR:
            s.numSwitches += 1
    
        s.nSamples.append(s.BW)
        s.BW = max(interpolateBWInterval(s.CLOCK, s.usedBWArray, s.bwArray), 0.01)  # interpolate bandwidth for the next heartbeat interval
        s.usedBWArray.append(s.BW)  # save the bandwidth used in the session
    
    if s.BLEN > 0:
        s.PLAYTIME += s.BLEN
    AVG_SESSION_BITRATE_sum = s.AVG_SESSION_BITRATE
    s.AVG_SESSION_BITRATE, s.REBUF_RATIO, s.rebuf_groundtruth = generateStats(s.AVG_SESSION_BITRATE, s.BUFFTIME, s.PLAYTIME, s.bufftimems, s.playtimems)
    s.allPerf[str(s.upr) + " " + str(s.initialBSM)] = str(s.AVG_SESSION_BITRATE) + " " + str(s.REBUF_RATIO)+" " + str(s.PLAYTIME)+" " + str(s.BUFFTIME)+" " + str(AVG_SESSION_BITRATE_sum)
    
    print s.trace_file + " initialBSM: "+str(bola_gp)+" minCell: "+str(s.minCellSize)+" QoE: " + str(s.maxQoE) + " avg. bitrate: " + str(s.AVG_SESSION_BITRATE) +  " buf. ratio: " + str(s.REBUF_RATIO) +" playtime: " + str(s.PLAYTIME) +" buftime: " + str(s.BUFFTIME)
