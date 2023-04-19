package quic

import (
	"time"

	"github.com/lucas-clemente/pstream/ackhandler"
	"github.com/lucas-clemente/pstream/congestion"
	"github.com/lucas-clemente/pstream/internal/protocol"
	"github.com/lucas-clemente/pstream/internal/utils"
	"github.com/lucas-clemente/pstream/internal/wire"
)

// PacketList ytxing
type PacketList struct {
	queue    []*packedFrames //ytxing: some frames are supposed to be a packet but not sealed.
	len      int             // ytxing: how many packet
	toPathid protocol.PathID
}

type packedFrames struct {
	frames    []wire.Frame //ytxing: a slice of a slice of frames.
	queueTime time.Time
}

//ytxing: for SE-ECF
const beta uint64 = 4

//GetPathSmoothedRTT get smoothed RTT in time.Duration
//ytxing
func GetPathSmoothedRTT(pth *path) time.Duration {
	return pth.rttStats.SmoothedRTT()

}

func (sch *scheduler) selectPathRoundRobin(s *session, hasRetransmission bool, hasStreamRetransmission bool, fromPth *path) *path {
	if sch.quotas == nil {
		sch.quotas = make(map[protocol.PathID]uint)
	}

	// XXX Avoid using PathID 0 if there is more than 1 path
	if len(s.paths) <= 1 {
		if !hasRetransmission && !s.paths[protocol.InitialPathID].SendingAllowed() {
			return nil
		}
		return s.paths[protocol.InitialPathID]
	}

	// TODO cope with decreasing number of paths (needed?)
	var selectedPath *path
	var lowerQuota, currentQuota uint
	var ok bool

	// Max possible value for lowerQuota at the beginning
	lowerQuota = ^uint(0)

pathLoop:
	for pathID, pth := range s.paths {
		// Don't block path usage if we retransmit, even on another path
		if !hasRetransmission && !pth.SendingAllowed() {
			continue pathLoop
		}

		// If this path is potentially failed, do no consider it for sending
		if pth.potentiallyFailed.Get() {
			continue pathLoop
		}

		// XXX Prevent using initial pathID if multiple paths
		if pathID == protocol.InitialPathID {
			continue pathLoop
		}

		currentQuota, ok = sch.quotas[pathID]
		if !ok {
			sch.quotas[pathID] = 0
			currentQuota = 0
		}

		if currentQuota < lowerQuota {
			selectedPath = pth
			lowerQuota = currentQuota
		}
	}

	return selectedPath

}

func (sch *scheduler) selectPathLowLatency(s *session, hasRetransmission bool, hasStreamRetransmission bool, fromPth *path) *path {
	utils.Debugf("ytxing: using selectPathLowLatency")
	// XXX Avoid using PathID 0 if there is more than 1 path
	if len(s.paths) <= 1 {
		if !hasRetransmission && !s.paths[protocol.InitialPathID].SendingAllowed() {
			return nil
		}
		return s.paths[protocol.InitialPathID]
	}

	// FIXME Only works at the beginning... Cope with new paths during the connection
	if hasRetransmission && hasStreamRetransmission && fromPth.rttStats.SmoothedRTT() == 0 {
		// Is there any other path with a lower number of packet sent?
		currentQuota := sch.quotas[fromPth.pathID]
		for pathID, pth := range s.paths {
			if pathID == protocol.InitialPathID || pathID == fromPth.pathID {
				continue
			}
			// The congestion window was checked when duplicating the packet
			if sch.quotas[pathID] < currentQuota {
				return pth
			}
		}
	}

	var selectedPath *path
	var lowerRTT time.Duration
	var currentRTT time.Duration
	selectedPathID := protocol.PathID(255)

pathLoop:
	for pathID, pth := range s.paths {
		// Don't block path usage if we retransmit, even on another path
		if !hasRetransmission && !pth.SendingAllowed() {
			continue pathLoop
		}

		// If this path is potentially failed, do not consider it for sending
		if pth.potentiallyFailed.Get() {
			continue pathLoop
		}

		// XXX Prevent using initial pathID if multiple paths
		if pathID == protocol.InitialPathID {
			continue pathLoop
		}

		currentRTT = pth.rttStats.SmoothedRTT()

		// Prefer staying single-path if not blocked by current path
		// Don't consider this sample if the smoothed RTT is 0
		if lowerRTT != 0 && currentRTT == 0 {
			continue pathLoop
		}

		// Case if we have multiple paths unprobed, prefer path with smaller quota(packet sent per path)
		if currentRTT == 0 {
			currentQuota, ok := sch.quotas[pathID]
			if !ok {
				sch.quotas[pathID] = 0
				currentQuota = 0
			}
			lowerQuota, _ := sch.quotas[selectedPathID]
			if selectedPath != nil && currentQuota > lowerQuota {
				continue pathLoop
			}
		}

		if currentRTT != 0 && lowerRTT != 0 && selectedPath != nil && currentRTT >= lowerRTT {
			continue pathLoop
		}

		// Update
		lowerRTT = currentRTT
		selectedPath = pth
		selectedPathID = pathID
	}

	// s.streamScheduler.schedule() //ytxing: this waste so much time
	// if currestNode != nil {
	// 	utils.Debugf("ytxing: s.streamScheduler.schedule return %v\n", currestNode.stream.streamID)
	// } else {
	// 	utils.Debugf("ytxing: s.streamScheduler.schedule return nil\n")
	// }

	// utils.Debugf("send on path %v", selectedPath.pathID)
	if selectedPath != nil {
		utils.Debugf("ytxing: GetPathBandwidth() path %v bwd %v mbps", selectedPath.pathID, selectedPath.GetPathBandwidth()/1e6)
	}
	return selectedPath
}
func (sch *scheduler) selectPathEarliestCompletionFirst(s *session, hasRetransmission bool, hasStreamRetransmission bool, fromPth *path) *path {
	// Avoid using PathID 0 if there is more than 1 path
	if len(s.paths) <= 1 {
		if !hasRetransmission && !s.paths[protocol.InitialPathID].SendingAllowed() {
			return nil
		}
		return s.paths[protocol.InitialPathID]
	}

	// FIXME Only works at the beginning... Cope with new paths during the connection
	if hasRetransmission && hasStreamRetransmission && fromPth.rttStats.SmoothedRTT() == 0 {
		// Is there any other path with a lower number of packet sent?
		currentQuota := sch.quotas[fromPth.pathID]
		for pathID, pth := range s.paths {
			if pathID == protocol.InitialPathID || pathID == fromPth.pathID {
				continue
			}
			// The congestion window was checked when duplicating the packet
			if sch.quotas[pathID] < currentQuota {
				return pth
			}
		}
	}

	var bestPath *path
	var secondBestPath *path
	var lowerRTT time.Duration
	var currentRTT time.Duration
	var secondLowerRTT time.Duration
	bestPathID := protocol.PathID(255)

pathLoop:
	for pathID, pth := range s.paths {
		// If this path is potentially failed, do not consider it for sending
		if pth.potentiallyFailed.Get() {
			continue pathLoop
		}

		// XXX: Prevent using initial pathID if multiple paths
		if pathID == protocol.InitialPathID {
			continue pathLoop
		}

		currentRTT = pth.rttStats.SmoothedRTT()

		// Prefer staying single-path if not blocked by current path
		// Don't consider this sample if the smoothed RTT is 0
		if lowerRTT != 0 && currentRTT == 0 {
			continue pathLoop
		}

		// Case if we have multiple paths unprobed
		if currentRTT == 0 {
			currentQuota, ok := sch.quotas[pathID]
			if !ok {
				sch.quotas[pathID] = 0
				currentQuota = 0
			}
			lowerQuota := sch.quotas[bestPathID]
			if bestPath != nil && currentQuota > lowerQuota {
				continue pathLoop
			}
		}

		if currentRTT >= lowerRTT {
			// Update second best available path
			if (secondLowerRTT == 0 || currentRTT < secondLowerRTT) && pth.SendingAllowed() {
				secondLowerRTT = currentRTT
				secondBestPath = pth
			}

			if currentRTT != 0 && lowerRTT != 0 && bestPath != nil {
				continue pathLoop
			}
		}

		// Update
		lowerRTT = currentRTT
		bestPath = pth
		bestPathID = pathID
	}

	// Unlikely
	if bestPath == nil {
		if secondBestPath != nil {
			return secondBestPath
		}
		return nil
	}

	// Allow retransmissions even if best path is blocked
	if hasRetransmission || bestPath.SendingAllowed() {
		return bestPath
	}

	// Stop looking if second best path is nil
	if secondBestPath == nil {
		return nil
	}

	// Else, check if it is beneficial to send on second best path
	var queueSize uint64
	getQueueSize := func(s *stream) (bool, error) {
		if s != nil {
			queueSize = queueSize + uint64(s.lenOfDataForWriting()) //ytxing!!! TOCOPY
		}

		return true, nil
	}
	s.streamsMap.Iterate(getQueueSize)

	cwndBest := uint64(bestPath.GetCongestionWindow())
	cwndSecond := uint64(secondBestPath.GetCongestionWindow())
	deviationBest := uint64(bestPath.rttStats.MeanDeviation())
	deviationSecond := uint64(secondBestPath.rttStats.MeanDeviation())

	delta := deviationBest
	if deviationBest < deviationSecond {
		delta = deviationSecond
	}

	xBest := queueSize
	// if queueSize < cwndBest
	if queueSize > cwndBest {
		xBest = cwndBest
	}

	lhs := uint64(lowerRTT) * (xBest + cwndBest)
	rhs := cwndBest * (uint64(secondLowerRTT) + delta)
	if beta*lhs < (beta*rhs + uint64(sch.waiting)*rhs) {
		xSecond := queueSize
		if queueSize < cwndSecond {
			xSecond = cwndSecond
		}
		lhsSecond := uint64(secondLowerRTT) * xSecond
		rhsSecond := cwndSecond * (2*uint64(lowerRTT) + delta)

		if lhsSecond > rhsSecond {
			sch.waiting = 1
			return nil
		}
	} else {
		sch.waiting = 0
	}
	return secondBestPath
}

func (sch *scheduler) selectPathStreamAwareEarliestCompletionFirst(s *session, hasRetransmission bool, hasStreamRetransmission bool, fromPth *path) *path {
	if s.streamScheduler == nil {
		return sch.selectPathEarliestCompletionFirst(s, hasRetransmission, hasStreamRetransmission, fromPth)
	}
	utils.Debugf("ytxing: selectPathStreamAwareEarliestCompletionFirst IN")
	// Reset selected stream. Best path always sends next stream in turn
	s.streamScheduler.toSend = nil

	// Avoid using PathID 0 if there is more than 1 path
	if len(s.paths) <= 1 {
		if !hasRetransmission && !s.paths[protocol.InitialPathID].SendingAllowed() {
			return nil
		}
		return s.paths[protocol.InitialPathID]
	}

	// FIXME Only works at the beginning... Cope with new paths during the connection
	if hasRetransmission && hasStreamRetransmission && fromPth.rttStats.SmoothedRTT() == 0 {
		// Is there any other path with a lower number of packet sent?
		currentQuota := sch.quotas[fromPth.pathID]
		for pathID, pth := range s.paths {
			if pathID == protocol.InitialPathID || pathID == fromPth.pathID {
				continue
			}
			// The congestion window was checked when duplicating the packet
			if sch.quotas[pathID] < currentQuota {
				return pth
			}
		}
	}

	var bestPath *path
	var secondBestPath *path
	var lowerRTT time.Duration
	var currentRTT time.Duration
	var secondLowerRTT time.Duration
	bestPathID := protocol.PathID(255)

pathLoop:
	for pathID, pth := range s.paths {
		// If this path is potentially failed, do not consider it for sending
		if pth.potentiallyFailed.Get() {
			continue pathLoop
		}

		// XXX: Prevent using initial pathID if multiple paths
		if pathID == protocol.InitialPathID {
			continue pathLoop
		}

		currentRTT = pth.rttStats.SmoothedRTT()

		// Prefer staying single-path if not blocked by current path
		// Don't consider this sample if the smoothed RTT is 0
		if lowerRTT != 0 && currentRTT == 0 {
			continue pathLoop
		}

		// Case if we have multiple paths unprobed
		if currentRTT == 0 {
			currentQuota, ok := sch.quotas[pathID]
			if !ok {
				sch.quotas[pathID] = 0
				currentQuota = 0
			}
			lowerQuota, _ := sch.quotas[bestPathID]
			if bestPath != nil && currentQuota > lowerQuota {
				continue pathLoop
			}
		}

		if currentRTT >= lowerRTT {
			// Update second best available path
			if (secondLowerRTT == 0 || currentRTT < secondLowerRTT) && pth.SendingAllowed() {
				secondLowerRTT = currentRTT
				secondBestPath = pth
			}

			if currentRTT != 0 && lowerRTT != 0 && bestPath != nil {
				continue pathLoop
			}
		}

		// Update
		lowerRTT = currentRTT
		bestPath = pth
		bestPathID = pathID
	}

	// Unlikely
	if bestPath == nil {
		if secondBestPath != nil {
			return secondBestPath
		}
		return nil
	}

	// Allow retransmissions even if best path is blocked
	if hasRetransmission || bestPath.SendingAllowed() {
		return bestPath
	}

	// Stop looking if second best path is nil
	if secondBestPath == nil {
		return nil
	}

	var queueSize uint64
	getQueueSize := func(s *stream) (bool, error) {
		if s != nil {
			queueSize = queueSize + uint64(s.lenOfDataForWriting())
		}

		return true, nil
	}
	s.streamsMap.Iterate(getQueueSize)

	visited := make(map[protocol.StreamID]bool)
	i := 0
	for len(visited) < s.streamScheduler.openStreams && i < s.streamScheduler.openStreams /* Should find a better way to deal with blocked streams */ {
		i++

		strm := s.streamScheduler.wrrSchedule() //ytxing: 自己写一个返回stream的函数来
		if strm == nil {
			break
		}

		if visited[strm.id] {
			strm.skip()
			continue
		}
		visited[strm.id] = true

		k := uint64(s.streamScheduler.bytesUntilCompletion(strm))

		// To cope with streams that are about to finish
		if queueSize > k {
			queueSize = k
		}

		cwndBest := uint64(bestPath.GetCongestionWindow())
		cwndSecond := uint64(secondBestPath.GetCongestionWindow())
		deviationBest := uint64(bestPath.rttStats.MeanDeviation())
		deviationSecond := uint64(secondBestPath.rttStats.MeanDeviation())

		delta := deviationBest
		if deviationBest < deviationSecond {
			delta = deviationSecond
		}

		xBest := queueSize
		// if queueSize > cwndBest {
		// 	xBest = cwndBest
		// } //zy: change to the descriptiom as paper

		lhs := uint64(lowerRTT) * (xBest + cwndBest)
		rhs := cwndBest * (uint64(secondLowerRTT) + delta)
		if beta*lhs < (beta*rhs + uint64(strm.waiting)*rhs) {
			xSecond := queueSize
			if queueSize < cwndSecond {
				xSecond = cwndSecond
			}
			lhsSecond := uint64(secondLowerRTT) * xSecond
			rhsSecond := cwndSecond * (2*uint64(lowerRTT) + delta)

			if lhsSecond > rhsSecond {
				strm.waiting = 1
				continue
			}
		} else {
			strm.waiting = 0
		}
		return secondBestPath
	}

	return nil
}

/*  ytxing:	Here we got a specific stream selected by myChooseStream, and
/			we choose a path with shortest packet arrival time.
/			Calculate pkt arrival time by assuming that the next packet is
/			of the maxSize.
*/
func (sch *scheduler) mySelectPathByArrivalTime(s *session, hasRetransmission bool, hasStreamRetransmission bool, fromPth *path) (selectedPath *path) {
	utils.Debugf("ytxing: mySelectPathByArrivalTime() IN\n")
	defer utils.Debugf("ytxing:  mySelectPathByArrivalTime() OUT\n")
	if s.perspective == protocol.PerspectiveClient {
		utils.Debugf("ytxing: I am client, use minRTT\n")
		return sch.selectPathLowLatency(s, hasRetransmission, hasStreamRetransmission, fromPth)
	}
	// XXX Avoid using PathID 0 if there is more than 1 path
	if len(s.paths) <= 1 {
		if !s.paths[protocol.InitialPathID].SendingAllowed() {
			return nil
		}
		selectedPath = s.paths[protocol.InitialPathID]
		return selectedPath
	}
	// FIXME Only works at the beginning... Cope with new paths during the connection
	if hasRetransmission && hasStreamRetransmission && fromPth.rttStats.SmoothedRTT() == 0 {
		// Is there any other path with a lower number of packet sent?
		currentQuota := sch.quotas[fromPth.pathID]
		for pathID, pth := range s.paths {
			if pathID == protocol.InitialPathID || pathID == fromPth.pathID {
				continue
			}
			// The congestion window was checked when duplicating the packet
			if sch.quotas[pathID] < currentQuota {
				utils.Debugf("ytxing: Strange return path %v\n", pth.pathID)
				return pth
			}
		}
	}

	for _, pth := range s.paths {
		if pth != nil && !sch.sendingQueueEmpty(pth) {
			if pth.SendingAllowed() {
				// utils.Debugf("ytxing: when selecting path, find path %v can send some stored frames\n", pathID)
				return pth
			}
			// utils.Debugf("ytxing: when selecting path, find path %v can send some stored frames but blocked\n", pathID)
		}
	}
	// var currentRTT time.Duration
	var currentArrivalTime time.Duration
	var lowerArrivalTime time.Duration
	selectedPathID := protocol.PathID(255)
	var allCwndLimited bool = true

	//find the best path, including that is limited by SendingAllowed()
pathLoop:
	for pathID, pth := range s.paths {

		// If this path is potentially failed, do not consider it for sending
		if pth.potentiallyFailed.Get() {
			// utils.Debugf("ytxing: path %v pth.potentiallyFailed.Get(), pass it", pathID)
			continue pathLoop
		}

		// XXX Prevent using initial pathID if multiple paths
		if pathID == protocol.InitialPathID {
			// utils.Debugf("ytxing: path %v pathID == protocol.InitialPathID, pass it", pathID)
			continue pathLoop
		}

		//ytxing: return nil if all paths are limited by cwnd
		allCwndLimited = allCwndLimited && (!hasRetransmission && !pth.SendingAllowed())

		// currentRTT = pth.rttStats.SmoothedRTT() //ytxing: if SmoothedRTT == 0, send on it. Because it will be duplicated to other paths. TODO maybe not?
		// currentArrivalTime, _ = sch.calculateArrivalTime(s, pth, false)
		currentArrivalTime, _ = sch.calculateArrivalTime(s, pth, false)
		// currentArrivalTime = pth.rttStats.SmoothedRTT()

		// Prefer staying single-path if not blocked by current path
		// Don't consider this sample if the smoothed RTT is 0
		if lowerArrivalTime != 0 && currentArrivalTime == 0 {
			continue pathLoop
		}

		// Case if we have multiple paths unprobed
		//ytxing: currentArrivalTime == 0 means rtt == 0
		if currentArrivalTime == 0 {
			currentQuota, ok := sch.quotas[pathID]
			if !ok {
				sch.quotas[pathID] = 0
				currentQuota = 0
			}
			lowerQuota, _ := sch.quotas[selectedPathID]
			utils.Debugf("ytxing: pathID %v, currentArrivalTime 0, currentQuota %v, selectedPathID %v, lowerQuota %v", pathID, currentQuota, selectedPathID, lowerQuota)
			if selectedPath != nil && currentQuota > lowerQuota {
				continue pathLoop
			}
		}

		if currentArrivalTime != 0 && lowerArrivalTime != 0 && selectedPath != nil && currentArrivalTime >= lowerArrivalTime { //ytxing: right?
			continue pathLoop
		}

		// Update
		lowerArrivalTime = currentArrivalTime
		selectedPath = pth
		selectedPathID = pathID
	}
	if allCwndLimited {
		utils.Debugf("ytxing: All paths are cwnd limited, block scheduling, return nil\n")
		return nil
	}
	return selectedPath //zy changes
/* zy already return
	var currestNode *node
	if s.streamScheduler.toSend == nil {
		utils.Debugf("ytxing: s.streamScheduler.toSend == nil\n")
		currestNode = s.streamScheduler.wrrSchedule() //ytxing: stupified!
		s.streamScheduler.toSend = currestNode
	} else {
		utils.Debugf("ytxing: s.streamScheduler.toSend != nil\n")
		currestNode = s.streamScheduler.toSend
	}
	//ytxing: TODO maybe some more checks
	if currestNode == nil {
		utils.Debugf("ytxing: currestStream == nil, seems to be crypto stream 1, find a minrtt path\n")
		return selectedPath
	}
	currestStream := currestNode.stream
	// if currestStream.lenOfDataForWriting() == 0 {
	// 	utils.Debugf("ytxing: Stream %d has no data for writing\n", currestStream.streamID)
	// 	// return nil
	// }

	//ytxing: case that the stream was previously sent on another path
	previousPathID, ok := sch.previousPath[currestStream.streamID]
	previousPath := s.paths[previousPathID]
	if ok && selectedPathID != previousPathID && previousPath != nil && selectedPath != nil {
		arrivalTimeOnPreviousPath, _ := sch.calculateArrivalTime(s, previousPath, false)
		currentArrivalTimeaddMeanDeviation, _ := sch.calculateArrivalTime(s, selectedPath, true)
		if arrivalTimeOnPreviousPath < currentArrivalTimeaddMeanDeviation {
			utils.Debugf("ytxing: current path%d -> previous path%d because of rtt jitter\n", selectedPathID, previousPath.pathID)
			utils.Debugf("ytxing: arrivalTimeOnPreviousPath %v, currentArrivalTimeaddMeanDeviation %v\n", arrivalTimeOnPreviousPath, currentArrivalTimeaddMeanDeviation)
			selectedPath = previousPath
		}
	}

	utils.Debugf("ytxing: selectedPathID %v sendingallow == %v\n", selectedPath.pathID, selectedPath.SendingAllowed())
	sch.previousPath[currestStream.streamID] = selectedPath.pathID
	return selectedPath
 */
}

// ytxing:	Calculate pkt arrival time by assuming that the next packet is of the MaxPacketSize. Return 0 if rtt == 0.
func (sch *scheduler) calculateArrivalTime(s *session, pth *path, addMeanDeviation bool) (time.Duration, bool) {

	packetSize := protocol.MaxPacketSize * 8               //bit uint64
	pthBwd := congestion.Bandwidth(pth.GetPathBandwidth()) // bit per second uint64
	utils.Debugf("ytxing: GetPathBandwidth() path %v bwd %v mbps", pth.pathID, pthBwd/1e6)
	inSecond := uint64(time.Second)
	var rtt time.Duration
	if addMeanDeviation {
		rtt = pth.rttStats.SmoothedRTT() + pth.rttStats.MeanDeviation()
		utils.Debugf("ytxing: addMeanDeviation path %d, rtt = rtt%v + MD%v", pth.pathID, pth.rttStats.SmoothedRTT(), pth.rttStats.MeanDeviation())
	} else {
		rtt = pth.rttStats.SmoothedRTT()

	}
	if pthBwd == 0 {
		utils.Debugf("ytxing: bandwidth of path %v is nil, arrivalTime == rtt/2 %v \n", pth.pathID, rtt/2)
		return rtt / 2, false
	}
	if rtt == 0 {
		utils.Debugf("ytxing: rtt of path%d is nil, arrivalTime == 0\n", pth.pathID)
		return 0, true
	}
	writeQueue, ok := sch.packetsNotSentYet[pth.pathID]
	var writeQueueSize protocol.ByteCount
	if !ok {
		writeQueueSize = 0
	} else {
		writeQueueSize = protocol.ByteCount(writeQueue.len) * protocol.DefaultTCPMSS * 8 //in bit
		//protocol.DefaultTCPMSS MaxPacketSize
	}

	arrivalTime := (uint64(packetSize+writeQueueSize)*inSecond)/uint64(pthBwd) + uint64(rtt)/2 //in nanosecond
	utils.Debugf("ytxing: arrivalTime of path %d is %v ms writeQueueSize %v bytes, pthBwd %v byte p s, rtt %v\n", pth.pathID, time.Duration(arrivalTime), writeQueueSize/8, pthBwd/8, rtt)
	return time.Duration(arrivalTime), true
}

// ytxing:	Calculate pkt arrival time by assuming that the next packet is of the MaxPacketSize. Return 0 if rtt == 0.
func (sch *scheduler) calculateArrivalTimeByRound(s *session, pth *path, addMeanDeviation bool) (time.Duration, bool) {

	packetSize := protocol.MaxPacketSize * 8 //bit uint64
	cwnd := pth.GetCongestionWindow()
	pthBwd := congestion.Bandwidth(pth.GetPathBandwidth()) // bit per second uint64
	utils.Debugf("ytxing: calculateArrivalTimeWithRound() path %v", pth.pathID)
	deltaRTT := pth.rttStats.GetDeltaMinRTT()

	var rtt time.Duration
	if addMeanDeviation {
		rtt = pth.rttStats.SmoothedRTT() + pth.rttStats.MeanDeviation()
		utils.Debugf("ytxing: addMeanDeviation path %d, rtt = rtt%v + MD%v", pth.pathID, pth.rttStats.SmoothedRTT(), pth.rttStats.MeanDeviation())
	} else {
		rtt = pth.rttStats.SmoothedRTT()

	}
	if pthBwd == 0 {
		utils.Debugf("ytxing: bandwidth of path %v is nil, arrivalTime == rtt/2 %v \n", pth.pathID, rtt/2)
		return rtt / 2, false
	}
	if rtt == 0 {
		utils.Debugf("ytxing: rtt of path%d is nil, arrivalTime == 0\n", pth.pathID)
		return 0, true
	}
	writeQueue, ok := sch.packetsNotSentYet[pth.pathID]
	var writeQueueSize protocol.ByteCount
	if !ok {
		writeQueueSize = 0
	} else {
		writeQueueSize = protocol.ByteCount(writeQueue.len) * protocol.DefaultTCPMSS * 8 //in bit
		//protocol.DefaultTCPMSS MaxPacketSize
	}

	round := int((packetSize + writeQueueSize) / cwnd)
	var arrivalTime time.Duration //in nanosecond
	for i := 0; i < round; i++ {
		arrivalTime += rtt + time.Duration(i)*deltaRTT
	}
	arrivalTime += (rtt + time.Duration(round)*deltaRTT) / 2
	utils.Debugf("ytxing: arrivalTime path %d is %v ms writeQueueSize %v bytes, round %v, deltaRTT %v\n", pth.pathID, time.Duration(arrivalTime), writeQueueSize/8, round, deltaRTT)
	return time.Duration(arrivalTime), true
}

//zy calculateroundbycwndminRTT
func (sch *scheduler) calculateArrivalTimeBycwndRound(s *session, pth *path, addMeanDeviation bool) (time.Duration, bool) {

	packetSize := protocol.MaxPacketSize * 8 //bit uint64
	cwnd := pth.GetCongestionWindow()
	pthBwd := congestion.Bandwidth(pth.GetPathBandwidth()) // bit per second uint64
	utils.Debugf("ytxing: calculateArrivalTimeWithRound() path %v", pth.pathID)
	deltacwndRTT := pth.rttStats.RecentcwndMinRTT() - pth.rttStats.LastcwndMinRTT()
	var rtt time.Duration
	if addMeanDeviation {
		rtt = pth.rttStats.SmoothedRTT() + pth.rttStats.MeanDeviation()
		utils.Debugf("ytxing: addMeanDeviation path %d, rtt = rtt%v + MD%v", pth.pathID, pth.rttStats.SmoothedRTT(), pth.rttStats.MeanDeviation())
	} else {
		rtt = pth.rttStats.SmoothedRTT()

	}
	if pthBwd == 0 {
		utils.Debugf("zy: bandwidth of path %v is nil, arrivalTime == rtt/2 %v \n", pth.pathID, rtt/2)
		return rtt / 2, false
	}
	if rtt == 0 {
		utils.Debugf("zy: rtt of path%d is nil, arrivalTime == 0\n", pth.pathID)
		return 0, true
	}
	writeQueue, ok := sch.packetsNotSentYet[pth.pathID]
	var writeQueueSize protocol.ByteCount
	if !ok {
		writeQueueSize = 0
	} else {
		writeQueueSize = protocol.ByteCount(writeQueue.len) * protocol.DefaultTCPMSS * 8 //in bit
		//protocol.DefaultTCPMSS MaxPacketSize
	}

	round := int((packetSize + writeQueueSize) / cwnd)
	var arrivalTime time.Duration //in nanosecond
	for i := 0; i < round; i++ {
		if (rtt + time.Duration(i)*deltacwndRTT) > pth.rttStats.MinRTT() {
			arrivalTime += rtt + time.Duration(i)*deltacwndRTT
		} else {
			arrivalTime += rtt + pth.rttStats.MinRTT()
		}

	}
	arrivalTime += (rtt + time.Duration(round)*deltacwndRTT) / 2
	utils.Debugf("zy: arrivalTime path %d is %v ms writeQueueSize %v bytes, round %v, deltacwndRTT %v\n", pth.pathID, time.Duration(arrivalTime), writeQueueSize/8, round, deltacwndRTT)
	return time.Duration(arrivalTime), true
}

// ytxing:	Calculate pkt arrival time by assuming that the next packet is of the MaxPacketSize. Return 0 if rtt == 0.
//TODO
func (sch *scheduler) calculateArrivalTimeWithGradient(s *session, pth *path, addMeanDeviation bool) (time.Duration, bool) {

	packetSize := protocol.MaxPacketSize * 8     //bit uint64
	pthBwd := pth.GetPathBandwidthByBytesAcked() // bit per second uint64
	utils.Debugf("ytxing: GetPathBandwidth() path %v bwd %v mbps", pth.pathID, pthBwd/1e6)
	inSecond := protocol.ByteCount(time.Second)
	gradientRTT := pth.rttStats.GetGradientRTT()

	var rtt time.Duration
	if addMeanDeviation {
		rtt = pth.rttStats.SmoothedRTT() + pth.rttStats.MeanDeviation()
		utils.Debugf("ytxing: addMeanDeviation path %d, rtt = rtt%v + MD%v", pth.pathID, pth.rttStats.SmoothedRTT(), pth.rttStats.MeanDeviation())
	} else {
		rtt = pth.rttStats.SmoothedRTT()

	}
	if pthBwd == 0 {
		utils.Debugf("ytxing: bandwidth of path %v is nil, arrivalTime == rtt/2 %v \n", pth.pathID, rtt/2)
		return rtt / 2, false
	}
	if rtt == 0 {
		utils.Debugf("ytxing: rtt of path%d is nil, arrivalTime == 0\n", pth.pathID)
		return 0, true
	}
	writeQueue, ok := sch.packetsNotSentYet[pth.pathID]
	var writeQueueSize protocol.ByteCount
	if !ok {
		writeQueueSize = 0
	} else {
		writeQueueSize = protocol.ByteCount(writeQueue.len) * protocol.DefaultTCPMSS * 8 //in bit
		//protocol.DefaultTCPMSS MaxPacketSize
	}
	waitingTime := time.Duration(((packetSize + writeQueueSize) * inSecond) / pthBwd)
	arrivalTime := waitingTime + (rtt+waitingTime*gradientRTT)/2 //in nanosecond
	utils.Debugf("ytxing: arrivalTime of path %d is %v writeQueueSize %v bytes, pthBwd %v byte p s, rtt %v \n", pth.pathID, time.Duration(arrivalTime), writeQueueSize/8, pthBwd/8, rtt)
	return arrivalTime, true
}

func (sch *scheduler) queueFrames(frames []wire.Frame, pth *path) {
	if sch.packetsNotSentYet[pth.pathID] == nil {
		sch.packetsNotSentYet[pth.pathID] = &PacketList{
			queue:    make([]*packedFrames, 0),
			len:      0,
			toPathid: pth.pathID,
		}
	}
	packetList := sch.packetsNotSentYet[pth.pathID]
	packetList.queue = append(packetList.queue, &packedFrames{frames, time.Now()})
	packetList.len += 1

	utils.Debugf("ytxing: queueFrames in path %d, total len %v len(list.queue) %v\n", pth.pathID, packetList.len, len(packetList.queue))
}

func (sch *scheduler) dequeueStoredFrames(pth *path) []wire.Frame {
	//TODO
	packetList := sch.packetsNotSentYet[pth.pathID]
	if len(packetList.queue) == 0 {
		return nil
	}
	packet := packetList.queue[0]
	// Shift the slice and don't retain anything that isn't needed.
	copy(packetList.queue, packetList.queue[1:])
	packetList.queue[len(packetList.queue)-1] = nil
	packetList.queue = packetList.queue[:len(packetList.queue)-1]
	// Update statistics
	packetList.len -= 1
	utils.Debugf("ytxing: dequeueStoredFrames in path %d, total len %v len(list.queue) %v \n", pth.pathID, packetList.len, len(packetList.queue))
	utils.Debugf("ytxing: this frame is queued for %v \n", time.Now().Sub(packet.queueTime))
	return packet.frames
}
func (sch *scheduler) sendingQueueEmpty(pth *path) bool {
	if sch.packetsNotSentYet[pth.pathID] == nil {
		sch.packetsNotSentYet[pth.pathID] = &PacketList{
			queue:    make([]*packedFrames, 0),
			len:      0,
			toPathid: pth.pathID,
		}
	}
	return len(sch.packetsNotSentYet[pth.pathID].queue) == 0
}

func (sch *scheduler) allSendingQueueEmpty() bool {

	for _, list := range sch.packetsNotSentYet {
		if len(list.queue) != 0 {
			return false
		}
	}
	utils.Debugf("ytxing: allSendingQueueEmpty\n")
	return true
}

func (sch *scheduler) dequeueStoredFramesFromOthers(pth *path) []wire.Frame {
	//TODO
	for pathID, list := range sch.packetsNotSentYet {
		if len(list.queue) != 0 {
			return sch.dequeueStoredFrames(pth.sess.paths[pathID])
		}
	}
	return nil
}

// Lock of s.paths must be free (in case of log print)
// ytxing: we now choose a path to sent, but not
func (sch *scheduler) performPacketSendingOfMine(s *session, windowUpdateFrames []*wire.WindowUpdateFrame, pth *path) (*ackhandler.Packet, bool, error) {
	utils.Debugf("ytxing: performPacketSendingOfMine() IN")
	defer utils.Debugf("ytxing: performPacketSendingOfMine() OUT")

	var err error
	var packet *packedPacket
	if pth.sentPacketHandler.ShouldSendRetransmittablePacket() {
		s.packer.QueueControlFrame(&wire.PingFrame{}, pth)
	}
	//ytxing START

	if pth.SendingAllowed() && sch.sendingQueueEmpty(pth) { //normally
		packet, err = s.packer.PackPacket(pth)
		utils.Debugf("ytxing: PackPacket()")
		if err != nil || packet == nil {
			return nil, false, err
		}
	} else if !pth.SendingAllowed() {
		stored, err := s.packer.StoreFrames(pth) //ytxing
		utils.Debugf("ytxing: path %v, !SendingAllowed() Stored!", pth.pathID)
		if stored {
			return nil, true, err //ytxing: here the "sent" bool is set to true, then the loop outside will not break
		} else {
			return nil, false, err //ytxing: here the "sent" bool is set to true, then the loop outside will not break
		}
	} else {
		packet, err = s.packer.PackPacketWithStoreFrames(pth)
		utils.Debugf("ytxing: PackPacketWithStoreFrames() path %v", pth.pathID)
		if err != nil || packet == nil {
			return nil, false, err
		}
	}
	//ytxing END

	// packet, err = s.packer.PackPacket(pth)
	// if err != nil || packet == nil {
	// 	return nil, false, err
	// }
	// original code

	if err = s.sendPackedPacket(packet, pth); err != nil {
		return nil, false, err
	}
	packets, retransmissions, losses := pth.sentPacketHandler.GetStatistics()
	utils.Debugf("ytxing: after sendPackedPacket() path %v, packets %v retransmissions %v, losses %v", pth.pathID, packets, retransmissions, losses)

	// send every window update twice
	for _, f := range windowUpdateFrames {
		s.packer.QueueControlFrame(f, pth)
	}

	// Packet sent, so update its quota
	sch.quotas[pth.pathID]++

	// Provide some logging if it is the last packet
	for _, frame := range packet.frames {
		switch frame := frame.(type) {
		case *wire.StreamFrame:
			if frame.FinBit {
				// Last packet to send on the stream, print stats
				s.pathsLock.RLock()
				utils.Infof("Info for stream %x of %x", frame.StreamID, s.connectionID)
				for pathID, pth := range s.paths {
					sntPkts, sntRetrans, sntLost := pth.sentPacketHandler.GetStatistics()
					rcvPkts := pth.receivedPacketHandler.GetStatistics()
					utils.Infof("Path %x: sent %d retrans %d lost %d; rcv %d rtt %v", pathID, sntPkts, sntRetrans, sntLost, rcvPkts, pth.rttStats.SmoothedRTT())
				}
				s.pathsLock.RUnlock()
			}
		default:
		}
	}

	pkt := &ackhandler.Packet{
		PacketNumber:    packet.number,
		Frames:          packet.frames,
		Length:          protocol.ByteCount(len(packet.raw)),
		EncryptionLevel: packet.encryptionLevel,
	}

	utils.Debugf("ytxing: Finally send pkt %v on path %v", pkt.PacketNumber, pth.pathID)
	return pkt, true, nil
}

func (sch *scheduler) sendPacketOriginal(s *session) error {
	utils.Debugf("ytxing: sendPacketOriginal() IN")
	defer utils.Debugf("ytxing: sendPacketOriginal() OUT")
	var pth *path
	// Update leastUnacked value of paths
	s.pathsLock.RLock()
	for _, pthTmp := range s.paths {
		pthTmp.SetLeastUnacked(pthTmp.sentPacketHandler.GetLeastUnacked())
	}
	s.pathsLock.RUnlock()

	// get WindowUpdate frames
	// this call triggers the flow controller to increase the flow control windows, if necessary
	windowUpdateFrames := s.getWindowUpdateFrames(false)
	for _, wuf := range windowUpdateFrames {
		s.packer.QueueControlFrame(wuf, pth)
	}

	// Repeatedly try sending until we don't have any more data, or run out of the congestion window
	// ytxing: OR packetsNotSentYet is not empty! TODO
	i := 0
	for {
		i++
		utils.Debugf("ytxing: =========================loop of sendPacketOriginal() IN Round No.%d============================", i)
		// We first check for retransmissions
		hasRetransmission, retransmitHandshakePacket, fromPth := sch.getRetransmission(s) //ytxing: hasRetransmission means there is something to retrans including control frames, and hasStreamRetransmission refers to normal frames
		// XXX There might still be some stream frames to be retransmitted
		hasStreamRetransmission := s.streamFramer.HasFramesForRetransmission()

		// Select the path here !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		s.pathsLock.RLock()
		pth = sch.selectPath(s, hasRetransmission, hasStreamRetransmission, fromPth)

		s.pathsLock.RUnlock()
		if pth != nil {
			utils.Debugf("ytxing: send on path %v", pth.pathID)
		} else {
			utils.Debugf("ytxing: path nil!")
		}

		// XXX No more path available, should we have a new QUIC error message?
		if pth == nil {
			windowUpdateFrames := s.getWindowUpdateFrames(false)
			return sch.ackRemainingPaths(s, windowUpdateFrames)
		}

		// If we have an handshake packet retransmission, do it directly
		if hasRetransmission && retransmitHandshakePacket != nil {
			s.packer.QueueControlFrame(pth.sentPacketHandler.GetStopWaitingFrame(true), pth)
			packet, err := s.packer.PackHandshakeRetransmission(retransmitHandshakePacket, pth)
			if err != nil {
				return err
			}
			if err = s.sendPackedPacket(packet, pth); err != nil {
				utils.Debugf("ytxing: sendPackedPacket, we have an handshake packet retransmission")
				return err
			}
			continue
		}

		// XXX Some automatic ACK generation should be done someway
		ack := pth.GetAckFrame()
		if ack != nil {
			s.packer.QueueControlFrame(ack, pth)
		}
		if ack != nil || hasStreamRetransmission {
			swf := pth.sentPacketHandler.GetStopWaitingFrame(hasStreamRetransmission)
			if swf != nil {
				s.packer.QueueControlFrame(swf, pth)
			}
		}

		// Also add CLOSE_PATH frames, if any
		for cpf := s.streamFramer.PopClosePathFrame(); cpf != nil; cpf = s.streamFramer.PopClosePathFrame() {
			s.packer.QueueControlFrame(cpf, pth)
		}

		// Also add ADD ADDRESS frames, if any
		for aaf := s.streamFramer.PopAddAddressFrame(); aaf != nil; aaf = s.streamFramer.PopAddAddressFrame() {
			s.packer.QueueControlFrame(aaf, pth)
		}

		// Also add PATHS frames, if any
		for pf := s.streamFramer.PopPathsFrame(); pf != nil; pf = s.streamFramer.PopPathsFrame() {
			s.packer.QueueControlFrame(pf, pth)
		}

		pkt, sent, err := sch.performPacketSendingOfMine(s, windowUpdateFrames, pth) //ytxing: HERE!! finally send a pkt

		if err != nil {
			return err
		}
		windowUpdateFrames = nil
		if sent && pkt == nil {
			utils.Debugf("ytxing: sent && pkt == nil")
			continue
		}

		if !sent {
			// Prevent sending empty packets
			return sch.ackRemainingPaths(s, windowUpdateFrames)
		}

		// Duplicate traffic when it was sent on an unknown performing path
		// FIXME adapt for new paths coming during the connection
		if pth.rttStats.SmoothedRTT() == 0 {
			currentQuota := sch.quotas[pth.pathID]
			// Was the packet duplicated on all potential paths?
		duplicateLoop:
			for pathID, tmpPth := range s.paths {
				if pathID == protocol.InitialPathID || pathID == pth.pathID {
					continue
				}
				if sch.quotas[pathID] < currentQuota && tmpPth.sentPacketHandler.SendingAllowed() && pkt != nil {
					// Duplicate it
					pth.sentPacketHandler.DuplicatePacket(pkt)
					break duplicateLoop
				}
			}
		}

		// And try pinging on potentially failed paths
		if fromPth != nil && fromPth.potentiallyFailed.Get() {
			err = s.sendPing(fromPth)
			if err != nil {
				return err
			}
		}
	}
}
