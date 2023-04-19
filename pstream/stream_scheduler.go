package quic

import (
	"errors"
	"fmt"
	"sync"

	"github.com/lucas-clemente/pstream/internal/protocol"
	"github.com/lucas-clemente/pstream/internal/utils"
	"github.com/lucas-clemente/pstream/internal/wire"
)

type streamScheduler struct {
	root         *node
	toSend       *node
	openStreams  int
	nodeMap      map[protocol.StreamID]*node
	streamFramer *streamFramer // Probably not needed anymore
	//blockedLast  bool
	// zy add Priority list
	//streamPriorityMap		map[uint8][]protocol.StreamID
	//streamPriorityList	[]uint8
	zeroQuantumStream []protocol.StreamID

	sortedList []protocol.StreamID
	//zy info for priority based RR
	startStreamIdPRR protocol.StreamID
	sync.RWMutex
}

type streamIterFunc func(*stream) (bool, error)

var (
	errNodeMapAccess = errors.New("streamsMap: Error accessing the streams node map")
)

//zy Copy from Pstream
func (sch *streamScheduler) iterateStreamID(streamID protocol.StreamID, fn streamIterFunc) (bool, error) {
	thisNode, ok := sch.nodeMap[streamID]
	if !ok {
		return true, errNodeMapAccess
	}
	return fn(thisNode.stream)
}

////ytxing: same in streamtree
// A Priority is a stream priority in QUIC (maybe move this to internal/protocol)
// type Priority struct {
// 	Dependency protocol.StreamID
// 	Weight     uint8
// 	Exclusive  bool
// }

// A node represents a stream in the dependency tree
type node struct {
	id              protocol.StreamID // Needed, since the stream may be nil
	stream          *stream
	weight          uint8  // actual weight is weight + 1
	childrensWeight uint32 // the weight of the node's children
	state           uint8  // states: nodeIdle, nodeActive, nodeClosed
	activeChildren  uint16 // number of active children
	quantum         uint16
	parent          *node
	children        []*node
	nextChild       uint16
	lowestQuantum   uint16
	numerator       uint64
	denominator     uint64

	waiting uint8 // waiting flag for SA-ECF

	currentWeight int ////ytxing: for smoothed round-robin
}

////ytxing: same in streamtree
// const (
// 	nodeIdle uint8 = iota
// 	nodeActive
// 	nodeClosed
// )

func newNodeSAECF(id protocol.StreamID, stream *stream, parent *node) *node {
	return &node{
		id:            id,
		stream:        stream,
		weight:        protocol.DefaultStreamWeight,
		parent:        parent,
		state:         nodeActive,
		lowestQuantum: 256,
		numerator:     1,
		denominator:   1,
		currentWeight: 0, //ytxing
	}
}

func newStreamScheduler() *streamScheduler {
	nodeMap := make(map[protocol.StreamID]*node)
	return &streamScheduler{
		root:    newNodeSAECF(0, nil, nil),
		nodeMap: nodeMap,
	}
}

////ytxing: same in streamtree
func (n *node) deactivateNode() error {
	// Try to keep node around as long as possible in order to maintain priority information
	// since the priority of a node may be altered even after its stream has finished
	// Idle branches should be kept around for at least 2 RTTs

	n.state = nodeClosed
	n.stream = nil
	if n.parent != nil && n.activeChildren == 0 {
		n.parent.removeWeight(n)
	}

	return nil
}

//zy sortedlist deactive
func (sch *streamScheduler) removeStreamFromSortedList(n *node) {
	streamId := n.id
	var index int
	for idx, id := range sch.sortedList {
		if id == streamId {
			index = idx
			break
		}
	}
	utils.Debugf("zy:stream %v out ", sch.sortedList[index])
	if index == len(sch.sortedList)-1 {

		sch.sortedList = sch.sortedList[:index]
	} else {
		sch.sortedList = append(sch.sortedList[:index], sch.sortedList[index+1:]...)
	}
}

// zy before deactiveteNode() call this func to change the streamPriorityMap and streamPriorityList
//func (sch *streamScheduler) removeStreamFromStreamScheduler(n *node) {
//	priority := n.weight
//	streamId := n.id
//	var index int
//	// TODO: Binary Search to improve the efficiency
//	// remove from stream priority map
//	for thisIndex, thisId := range sch.streamPriorityMap[priority] {
//		if thisId == streamId {
//			index = thisIndex
//			break
//		}
//	}
//	if index == 0 && len(sch.streamPriorityMap[priority]) == 1{
//		delete(sch.streamPriorityMap, priority)
//		var listIndex int
//		for thisIndex, thisPriority := range sch.streamPriorityList {
//			if thisPriority == priority {
//				listIndex = thisIndex
//				break
//			}
//		}
//		// remove from stream priority list
//		if listIndex != len(sch.streamPriorityList) - 1 {
//			sch.streamPriorityList = append(sch.streamPriorityList[:listIndex], sch.streamPriorityList[listIndex+1:]...)
//			sch.startStreamIdPRR = sch.streamPriorityMap[sch.streamPriorityList[listIndex]][0]
//		} else {
//			sch.streamPriorityList = sch.streamPriorityList[:listIndex]
//			if listIndex != 0 {
//				sch.startStreamIdPRR = sch.streamPriorityMap[sch.streamPriorityList[listIndex-1]][0]
//			} else {
//				sch.startStreamIdPRR = 0
//			}
//		}
//	} else if index != len(sch.streamPriorityMap[priority]) - 1 {
//		sch.streamPriorityMap[priority] = append(sch.streamPriorityMap[priority][:index], sch.streamPriorityMap[priority][index + 1:]...)
//		sch.startStreamIdPRR = sch.streamPriorityMap[priority][index]
//	} else {
//		sch.streamPriorityMap[priority] = sch.streamPriorityMap[priority][:index]
//		sch.startStreamIdPRR = sch.streamPriorityMap[priority][index - 1]
//	}
//	// remove from zero stream list
//	zeroIndex := -1
//	for idx, zeroId := range sch.zeroQuantumStream {
//		if zeroId == streamId {
//			zeroIndex = idx
//			break
//		}
//	}
//	if zeroIndex != -1 {
//		if zeroIndex == len(sch.zeroQuantumStream) - 1 {
//			sch.zeroQuantumStream = sch.zeroQuantumStream[:zeroIndex]
//		} else {
//			sch.zeroQuantumStream = append(sch.zeroQuantumStream[:zeroIndex], sch.zeroQuantumStream[zeroIndex + 1:]...)
//		}
//	}
//}

//ytxing: same in streamtree.
//Add a child to n
func (n *node) addWeight(child *node) {
	n.childrensWeight += uint32(child.weight) + 1
	n.activeChildren++
	n.children = append(n.children, child)
	utils.Debugf("ytxing: addWeight, add child  %v to , %v, total activeChildren %v", child.id, n.id, n.activeChildren)

	if n.parent != nil && n.state != nodeActive && n.activeChildren == 1 {
		n.parent.addWeight(n)
	}
}

//ytxing: same in streamtree
func (n *node) removeWeight(child *node) {
	index := 0
	for i, c := range n.children {
		if c == child {
			index = i
			break
		}
	}
	n.children = append(n.children[:index], n.children[index+1:]...)
	if len(n.children) == 0 {
		n.nextChild = 0
	} else {
		n.nextChild = n.nextChild % uint16(len(n.children))
	}

	n.childrensWeight -= uint32(child.weight) - 1
	n.activeChildren--

	if n.parent != nil && n.activeChildren == 0 {
		n.parent.removeWeight(n)
	}
}

//ytxing: nobody call you poor guy
func (n *node) skip() {
	n.quantum = 0
	if n.parent != nil {
		n.parent.nextChild = (n.parent.nextChild + 1) % uint16(len(n.parent.children))
		n.parent.skip()
	}
}

// Estimate the number of bytes which needs to be sent over the entire connection in order to complete the stream
func (sch *streamScheduler) bytesUntilCompletion(n *node) protocol.ByteCount {
	L := protocol.MaxPacketSize
	len := n.stream.lenOfDataForWriting()

	var left protocol.ByteCount
	if L < len {
		left = len - L
	} else {
		left = len
	}

	if protocol.ByteCount(n.quantum)*L >= left || sch.openStreams == 1 {
		//zychange parentlowestquantum not set
		return len
	}

	g := protocol.ByteCount(n.denominator - n.numerator)
	G := g * left
	return G + len/protocol.ByteCount(n.numerator)
}

// New nodes are intitially set to become the child of the root node
func (sch *streamScheduler) addNode(child *stream) error {
	defer sch.printTree()
	sch.Lock()
	defer sch.Unlock()

	if child == nil {
		return fmt.Errorf("attempt to add unknown node")
	}

	utils.Debugf("ytxing: in addNode, add stream %v ", child.streamID)
	if child.streamID == 1 /* Crypto stream handled separately */ {
		utils.Debugf("ytxing: in addNode, stream id == 1 ")
		return nil
	}

	// Set header stream as root
	if child.streamID == 3 {
		utils.Debugf("ytxing: in addNode, stream id == 3 ")
		sch.root.id = child.streamID
		sch.root.stream = child
		sch.root.state = nodeActive
		sch.nodeMap[3] = sch.root
		return nil
	}

	n := newNodeSAECF(child.streamID, child, sch.root)
	if n.state == nodeActive {
		sch.openStreams++
		sch.root.addWeight(n)
	}
	sch.nodeMap[child.streamID] = n
	utils.Debugf("ytxing: in addNode, stream id == %v ", child.streamID)

	return nil
}

func (sch *streamScheduler) maybeSetWeight(id protocol.StreamID, weight uint8) error {
	sch.Lock()
	defer sch.Unlock()

	if id == 1 || id == 3 /* Weight does not impact crypto and header stream */ {
		sch.sortedList = append(sch.sortedList, id)
		return nil
	}
	n, ok := sch.nodeMap[id]
	if !ok {
		return fmt.Errorf("setting weight of unknown stream %d", id)
	}
	if n.weight == weight {
		return nil
	}

	if n.state == nodeActive || n.activeChildren > 0 {
		diff := int(weight) - int(n.weight)
		newWeight := int(n.parent.childrensWeight) + diff
		n.parent.childrensWeight = uint32(newWeight)
	}

	n.weight = weight
	// zy add this weight to streamPriorityList
	//if _, ok := sch.streamPriorityMap[weight]; ok {
	//	sch.streamPriorityMap[weight] = append(sch.streamPriorityMap[weight], id)
	//}	else {
	//	sch.streamPriorityMap[weight] = []protocol.StreamID{id}
	//	sch.streamPriorityList = append(sch.streamPriorityList, weight)
	//	sort.Slice(sch.streamPriorityList, func(i int, j int) bool {
	//		return sch.streamPriorityList[i] > sch.streamPriorityList[j]
	//	})
	//}
	finalIndex := 0
	if len(sch.sortedList) == 0 {
		sch.sortedList = append(sch.sortedList, 3)
	}
	if sch.sortedList[len(sch.sortedList)-1] == 3 {
		sch.sortedList = append(sch.sortedList, id)
	} else {
		for index, streamID := range sch.sortedList {
			if streamID == 1 || streamID == 3 {
				continue
			} else {
				thisnode := sch.nodeMap[streamID]
				if thisnode.weight >= weight {
					utils.Debugf("liststream %v , listweight %v\n, index %v, stream %v, listweight %v", streamID, thisnode.weight, index, n.id, weight)
					continue
				} else {
					finalIndex = index
					break

				}
			}
		}

		if finalIndex == 0 {
			sch.sortedList = append(sch.sortedList, id)
		} else {

			sch.sortedList = append(sch.sortedList[:finalIndex], append([]protocol.StreamID{id}, sch.sortedList[finalIndex:]...)...)
		}
	}
	// for _, idx := range sch.sortedList {
	// 	utils.Infof("stream %v in stream list\n", idx)
	// }
	if n.currentWeight != 0 {
		utils.Infof("Reset stream %v weight, SWRR may go wrong\n")
	}
	n.currentWeight = 0
	return nil
}

func (sch *streamScheduler) maybeSetParent(childID, parentID protocol.StreamID, exclusive bool) error {
	sch.Lock()
	defer sch.Unlock()

	if childID == parentID {
		return fmt.Errorf("setting stream %d as its own parent", childID)
	}
	if childID == 1 {
		return fmt.Errorf("setting parent of crypto stream")
	}
	if childID == 3 {
		return fmt.Errorf("setting parent of header stream")
	}
	if parentID == 1 {
		return fmt.Errorf("setting parent to crypto stream")
	}
	if parentID == 0 {
		parentID = 3 // Is it really necessary that the root node has ID 0?
	}
	child, ok := sch.nodeMap[childID]
	if !ok {
		return fmt.Errorf("setting unknown stream %d as exclusive child of stream %d", childID, parentID)
	}
	if !exclusive && child.parent != nil && child.parent.id == parentID /* Already parent, nothing to do */ {
		return nil
	}
	newParent, ok := sch.nodeMap[parentID]
	if !ok {
		return fmt.Errorf("setting stream %d as exclusive11111 child of unknown stream %d", childID, parentID)
	}
	oldParent := child.parent

	// RFC 7540: If a stream is made dependent on one of its own dependencies, the
	// formerly dependent stream is first moved to be dependent on the
	// reprioritized stream's previous parent.  The moved dependency retains
	// its weight.
	for n := newParent.parent; n.parent != nil; n = n.parent {
		if n == child {
			if newParent.state == nodeActive || newParent.activeChildren > 0 {
				// Only active nodes are set as children
				newParent.parent.removeWeight(newParent)
				if oldParent != nil {
					oldParent.addWeight(newParent)
				}
			}
			newParent.parent = oldParent
		}
	}

	// Remove node from its previous parent
	if child.parent != nil {
		if child.state == nodeActive || child.activeChildren > 0 {
			child.parent.removeWeight(child)
		}

		child.parent = nil
	}

	// RFC 7540: Setting a dependency with the exclusive flag for a
	// reprioritized stream causes all the dependencies of the new parent
	// stream to become dependent on the reprioritized stream.
	if exclusive {
		for _, c := range newParent.children {
			if c != newParent {
				if c.state == nodeActive || c.activeChildren > 0 {
					child.addWeight(c)
					newParent.removeWeight(c)
				}

				c.parent = child
			}
		}
	}

	child.parent = newParent
	if child.state == nodeActive || child.activeChildren > 0 {
		newParent.addWeight(child)
	}

	return nil
}

func (sch *streamScheduler) setActive(id protocol.StreamID) error {
	sch.Lock()
	defer sch.Unlock()

	if id == 1 /* Crypto stream handled separatly */ {
		return nil
	}
	if id == 3 /* Header stream is always considered active */ {
		return nil
	}

	n, ok := sch.nodeMap[id]
	if !ok {
		return fmt.Errorf("setting unknown stream %d active", id)
	}

	n.state = nodeActive
	n.parent.addWeight(n)
	sch.openStreams++

	return nil
}

// Copied from stream_framer.go
// //ytxing: this is actually the streamLambda fn in maybePopNormalFrames but from one specific stream
func (sch *streamScheduler) send(s *stream, maxBytes protocol.ByteCount, pth *path) (res *wire.StreamFrame, currentLen protocol.ByteCount, cont bool) {
	frame := &wire.StreamFrame{DataLenPresent: true}

	if s == nil || s.streamID == 1 /* Crypto stream is handled separately */ {
		cont = true
		return
	}

	frame.StreamID = s.streamID
	// not perfect, but thread-safe since writeOffset is only written when getting data
	frame.Offset = s.writeOffset
	frameHeaderBytes, _ := frame.MinLength(protocol.VersionWhatever) // can never error

	//if currentLen+frameHeaderBytes > maxBytes {
	if frameHeaderBytes > maxBytes {
		cont = false // theoretically, we could find another stream that fits, but this is quite unlikely, so we stop here
		return
	}
	//maxLen := maxBytes - currentLen - frameHeaderBytes
	maxLen := maxBytes - frameHeaderBytes

	var sendWindowSize protocol.ByteCount
	lenStreamData := s.lenOfDataForWriting()
	if lenStreamData != 0 {
		sendWindowSize, _ = sch.streamFramer.flowControlManager.SendWindowSize(s.streamID)
		maxLen = utils.MinByteCount(maxLen, sendWindowSize)
	}

	if maxLen == 0 {
		cont = true
		return
	}

	var data []byte
	if lenStreamData != 0 {
		// Only getDataForWriting() if we didn't have data earlier, so that we
		// don't send without FC approval (if a Write() raced).
		data = s.getDataForWriting(maxLen)
	}

	// This is unlikely, but check it nonetheless, the scheduler might have jumped in. Seems to happen in ~20% of cases in the tests.
	shouldSendFin := s.shouldSendFin()
	if data == nil && !shouldSendFin {
		cont = true
		return
	}

	if shouldSendFin {
		frame.FinBit = true
		s.sentFin()
	}

	frame.Data = data
	sch.streamFramer.flowControlManager.AddBytesSent(s.streamID, protocol.ByteCount(len(data)))
	// Finally, check if we are now FC blocked and should queue a BLOCKED frame
	if sch.streamFramer.flowControlManager.RemainingConnectionWindowSize() == 0 {
		// We are now connection-level FC blocked
		sch.streamFramer.blockedFrameQueue = append(sch.streamFramer.blockedFrameQueue, &wire.BlockedFrame{StreamID: 0})
	} else if !frame.FinBit && sendWindowSize-frame.DataLen() == 0 {
		// We are now stream-level FC blocked
		sch.streamFramer.blockedFrameQueue = append(sch.streamFramer.blockedFrameQueue, &wire.BlockedFrame{StreamID: s.StreamID()})
	}

	//res = append(res, frame)
	res = frame
	//currentLen += frameHeaderBytes + frame.DataLen()
	currentLen = frameHeaderBytes + frame.DataLen()

	if currentLen == maxBytes {
		cont = false
		return
	}

	cont = true
	return
}

////ytxing:	TODO return one stream according to the stream tree, with WRR, will be called several time
func (sch *streamScheduler) scheduleSWRR() *stream {
	sch.Lock()
	defer sch.Unlock()
	parent := sch.root
	////ytxing TODO
	if parent.activeChildren > 0 {
		return nil
	}
	var bestChild *node
	var totalWeight int = 0
	for _, currentChild := range parent.children {
		totalWeight += int(currentChild.weight)
		currentChild.currentWeight += int(currentChild.weight)
		if bestChild == nil || currentChild.currentWeight > bestChild.currentWeight {
			bestChild = currentChild
		}
	}

	if bestChild == nil {
		return nil
	}

	bestChild.currentWeight -= totalWeight
	return bestChild.stream
}

func (sch *streamScheduler) traverse(n *node) (strm *node) {
	// Update quantum if the stream is selected in a new round
	if n.quantum == 0 {
		// n.quantum = uint16(n.weight) + 1
		n.quantum = uint16(n.weight)
	}

	// Gather additional info
	if n.parent != nil {
		if n.parent.activeChildren == 1 {
			n.lowestQuantum = n.parent.lowestQuantum
		} else {
			quantum := n.quantum - 1
			if quantum < n.quantum-1 {
				n.lowestQuantum = quantum
			} else {
				n.lowestQuantum = n.parent.lowestQuantum
			}
		}
		n.numerator = uint64(n.weight+1) * n.parent.numerator
		n.denominator = uint64(n.parent.childrensWeight) * n.parent.denominator
	}

	var sw protocol.ByteCount
	if n.stream != nil {
		sw, _ = sch.streamFramer.flowControlManager.SendWindowSize(n.stream.streamID)
	}

	if n.stream != nil && n.stream.finishedWriteAndSentFin() {
		sch.openStreams--
		sch.removeStreamFromSortedList(n)
		n.deactivateNode()
		utils.Debugf("ytxing: deactivateNode %v", n.id)
		return
	}
	if n.stream != nil {
		utils.Debugf("ytxing: traverse, stream %v , quantum %v, n.state %v, swnd %v, n.activeChildren %v, n.stream.lenOfDataForWriting() %v", n.id, n.quantum, n.state, sw, n.activeChildren, n.stream.lenOfDataForWriting())
	}
	if n.id == 3 && n.stream != nil && n.stream.lenOfDataForWriting() > 0 && sw > 0 {
		/* Special case for header stream, since it never closes, it always gets to send if it has sth */
		strm = n
		utils.Debugf("ytxing: traverse, stream %v has sth to send", n.id)
	} else if n.id != 3 && n.state == nodeActive && n.quantum > 0 && n.stream != nil && !n.stream.finishedWriteAndSentFin() && sw > 0 {
		n.quantum-- //ytxing: seems to be a WRR algorithm
		strm = n
		utils.Debugf("ytxing: traverse, stream %v has sth to send, quantum-- %v", n.id, n.quantum)
	} else if n.activeChildren > 0 && n.quantum > 0 {
		//ytxing: if a node has quantum, but nothing to send, then pass it to its children
		for i := 0; i < len(n.children); i++ {
			utils.Debugf("ytxing: traverse, to next child")
			c := n.children[n.nextChild]
			strm = sch.traverse(c)
			if strm != nil {
				n.quantum--
				break
			}
		}
	} /*else if n.parent != nil {
		n.parent.nextChild = (n.parent.nextChild + 1) % uint16(len(n.parent.children))
		return
	} */

	if (strm == nil || n.quantum == 0) && n.parent != nil && len(n.parent.children) > 0 {
		n.parent.nextChild = (n.parent.nextChild + 1) % uint16(len(n.parent.children)) //ytxing: for roundrobin to the node's siblings
	}

	return
}

func (sch *streamScheduler) wrrSchedule() *node {
	sch.Lock()
	defer sch.Unlock()
	utils.Debugf("ytxing: wrrschedule() IN \n")
	n := sch.traverse(sch.root)
	if n == nil {
		utils.Debugf("ytxing: wrrschedule() OUT, return stream nil")
	} else {
		utils.Debugf("ytxing: wrrschedule() OUT, return stream %v", n.id)
	}
	return n
}

func (sch *streamScheduler) findNextStream(streamID protocol.StreamID) protocol.StreamID {
	if streamID == sch.sortedList[len(sch.sortedList)-1] {
		return sch.sortedList[0]
	} else {
		for i := 0; i < sch.openStreams; i++ {
			if sch.sortedList[i] == streamID {
				return sch.sortedList[i+1]
			}
		}
	}
	return streamID
}

//zy find next stream to send by DFCFS
func (sch *streamScheduler) traverseDFCFS(ID protocol.StreamID, flag int) (strm *node) {

	if len(sch.sortedList) == 0 {
		return
	}
	var streamID protocol.StreamID
	if ID == 0 {
		streamID = sch.sortedList[0]
	} else {
		streamID = ID
	}
	streamNode := sch.nodeMap[streamID]
	if streamNode.stream != nil && streamNode.stream.finishedWriteAndSentFin() {
		sch.openStreams--
		sch.removeStreamFromSortedList(streamNode)
		streamNode.deactivateNode()
		utils.Debugf("zy: deactivateNode %v", streamNode.id)
		return
	}
	var sw protocol.ByteCount
	if streamNode.stream != nil {
		sw, _ = sch.streamFramer.flowControlManager.SendWindowSize(streamNode.stream.streamID)
	}
	if streamNode.stream != nil {
		utils.Debugf("ytxing: traverse, stream %v , quantum %v, n.state %v, swnd %v, n.activeChildren %v, n.stream.lenOfDataForWriting() %v", streamNode.id, streamNode.quantum, streamNode.state, sw, streamNode.activeChildren, streamNode.stream.lenOfDataForWriting())
	}
	if streamNode.id == 3 && streamNode.stream != nil && streamNode.stream.lenOfDataForWriting() > 0 && sw > 0 {
		/* Special case for header stream, since it never closes, it always gets to send if it has sth */
		strm = streamNode
		utils.Debugf("ytxing: traverse, stream %v has sth to send", streamNode.id)
	} else if streamNode.id != 3 && streamNode.state == nodeActive && streamNode.stream != nil && !streamNode.stream.finishedWriteAndSentFin() && sw > 0 {
		strm = streamNode
		utils.Debugf("ytxing: traverse, stream %v has sth to send", streamNode.id)
	} else if flag == 1 {
		nextStream := streamID
		for i := 0; i < sch.openStreams; i++ {
			nextStream = sch.findNextStream(nextStream)
			strm = sch.traverseDFCFS(nextStream, 0)
			if strm != nil {
				break
			}
		}
	}
	return
}

//zy find next stream in the streamPriorityMap
//func (sch *streamScheduler) findNextStream(Id protocol.StreamID ) *node {
//	if Id == 1 {
//		thisNode, ok := sch.nodeMap[3]
//		if !ok {
//			if len(sch.streamPriorityList) > 0 {
//				return sch.nodeMap[sch.streamPriorityMap[sch.streamPriorityList[0]][0]]
//			}
//		} else {
//			return thisNode
//		}
//	}	else if Id == 3 {
//		if len(sch.streamPriorityList) > 0 {
//			return sch.nodeMap[sch.streamPriorityMap[sch.streamPriorityList[0]][0]]
//		}
//	}
//	thisPriority := sch.nodeMap[Id].weight
//	var index int
//	for i, j := range sch.streamPriorityMap[thisPriority] {
//		if j == Id {
//			index = i
//			break
//		}
//	}
//	if index == len (sch.streamPriorityMap[thisPriority]) - 1 {
//		for i, j := range sch.streamPriorityList {
//			if j == thisPriority {
//				if i == len(sch.streamPriorityList) - 1 {
//					return nil
//				} else {
//					return sch.nodeMap[sch.streamPriorityMap[sch.streamPriorityList[i + 1]][0]]
//				}
//			}
//		}
//	}	else {
//		return sch.nodeMap[sch.streamPriorityMap[thisPriority][index + 1]]
//	}
//	return nil
//}

// zy add dynamic FCFS scheduler
func (sch *streamScheduler) dynamicFCFSSchedule() *node {
	sch.Lock()
	defer sch.Unlock()
	utils.Debugf("zy: DFCFSschedule() IN \n")
	n := sch.traverseDFCFS(0, 1)
	if n == nil {
		utils.Debugf("zy: DFCFSschedule() OUT, return stream nil")
	} else {
		utils.Debugf("zy: DFCFSschedule() OUT, return stream %v", n.id)
	}
	return n
}

//zy TODO
// zy add priority based RR scheduler

func (sch *streamScheduler) PriorityBasedRRScheduler(fn streamIterFunc) error {
	sch.Lock()
	defer sch.Lock()

	for _, i := range []protocol.StreamID{1, 3} {
		cont, err := sch.iterateStreamID(i, fn)
		if err != nil && err != errNodeMapAccess {
			return err
		}
		if !cont {
			return nil
		}
	}
	for i := 0; i < sch.openStreams; i++ {
		var streamID protocol.StreamID
		if sch.startStreamIdPRR == 0 {
			streamID = sch.sortedList[i]
			sch.startStreamIdPRR = streamID
		} else {
			streamID = sch.startStreamIdPRR
		}
		if streamID == 1 || streamID == 3 {
			continue
		}
		sch.startStreamIdPRR = sch.findNextStream(streamID)
		thisNode := sch.nodeMap[streamID]
		currentHighWeight := uint8(0)
		for _, id := range sch.sortedList {
			if id != 1 && id != 3 {
				currentHighWeight = sch.nodeMap[id].weight
				break
			}
		}
		if thisNode.quantum == 0 && thisNode.weight != currentHighWeight {
			continue
		} else if thisNode.quantum == 0 && thisNode.weight == currentHighWeight {
			for _, zeroId := range sch.zeroQuantumStream {
				zeroNode := sch.nodeMap[zeroId]
				zeroNode.quantum = uint16(zeroNode.weight + 1)
			}
			sch.zeroQuantumStream = sch.zeroQuantumStream[0:0]
		}

		cont, err := sch.iterateStreamID(streamID, fn)
		if err != nil {
			return err
		}
		if !cont {
			thisNode.quantum--
			if thisNode.quantum == 0 {
				sch.zeroQuantumStream = append(sch.zeroQuantumStream, streamID)
			}
			break
		}
	}
	return nil
}

//printTree print all nodes with level order
func (sch *streamScheduler) printTree() {

	var dfs func(*node, uint32, map[protocol.StreamID]uint32)

	dfs = func(n *node, level uint32, res map[protocol.StreamID]uint32) {

		if n.stream != nil {
			res[n.id] = level
			utils.Debugf("ytxing: stream %v n.activeChildren %v \n", n.id, n.activeChildren)
		}

		if n.activeChildren > 0 {
			//traverse child
			for i := 0; i < len(n.children); i++ {
				c := n.children[n.nextChild]

				utils.Debugf("ytxing: nextChild stream %v\n", c.id)
				dfs(c, level+1, res)
				n.nextChild = (n.nextChild + 1) % uint16(len(n.children))
			}
		}
		return
	}

	res := make(map[protocol.StreamID]uint32)
	dfs(sch.root, 0, res)
	if utils.Debug() {
		utils.Debugf("print out StreamScheduler:\n")
	}
	for k, v := range res {
		if utils.Debug() {
			utils.Debugf("streamID: %d, level %d\n", k, v)
		}
	}
}

func (sch *streamScheduler) renewQuantum() {
	for _, zeroId := range sch.zeroQuantumStream {
		zeroNode := sch.nodeMap[zeroId]
		zeroNode.quantum = uint16(zeroNode.weight)
	}
	sch.zeroQuantumStream = sch.zeroQuantumStream[0:0]
}
func (sch *streamScheduler) traversePRR(ID protocol.StreamID, flag int) (strm *node) {

	if len(sch.sortedList) == 0 {
		return
	}
	var streamID protocol.StreamID
	if ID == 0 {
		streamID = sch.sortedList[0]
	} else {
		streamID = ID
	}
	streamNode := sch.nodeMap[streamID]
	sch.startStreamIdPRR = sch.findNextStream(streamID)
	utils.Infof("next stream %v\n", sch.startStreamIdPRR)
	if streamNode.stream != nil && streamNode.stream.finishedWriteAndSentFin() {
		sch.openStreams--
		sch.removeStreamFromSortedList(streamNode)
		streamNode.deactivateNode()
		utils.Infof("zy: deactivateNode %v", streamNode.id)
		return
	}
	var sw protocol.ByteCount
	if streamNode.stream != nil {
		sw, _ = sch.streamFramer.flowControlManager.SendWindowSize(streamNode.stream.streamID)
	}
	if streamNode.stream != nil {
		utils.Debugf("ytxing: traverse, stream %v , quantum %v, n.state %v, swnd %v, n.activeChildren %v, n.stream.lenOfDataForWriting() %v, next stream %v", streamNode.id, streamNode.quantum, streamNode.state, sw, streamNode.activeChildren, streamNode.stream.lenOfDataForWriting(), sch.startStreamIdPRR)
	}
	if streamNode.id == 3 && streamNode.stream != nil && streamNode.stream.lenOfDataForWriting() > 0 && sw > 0 {
		/* Special case for header stream, since it never closes, it always gets to send if it has sth */
		strm = streamNode
		utils.Debugf("ytxing: traverse, stream %v has sth to send", streamNode.id)
	} else if streamNode.id != 3 && streamNode.state == nodeActive && streamNode.stream != nil && !streamNode.stream.finishedWriteAndSentFin() && sw > 0 {

		if streamNode.quantum == 0 {
			zeroflag := 0
			for _, zeroId := range sch.zeroQuantumStream {
				if zeroId == streamID {
					zeroflag = 1
					break
				}
			}
			if zeroflag == 0 {
				streamNode.quantum = uint16(streamNode.weight)
				strm = streamNode
			}
			return
		}
		streamNode.quantum--
		if streamNode.quantum == 0 {
			sch.zeroQuantumStream = append(sch.zeroQuantumStream, streamID)
			currentHighWeight := uint8(0)
			for _, id := range sch.sortedList {
				if id != 1 && id != 3 {
					currentHighWeight = sch.nodeMap[id].weight
					break
				}
			}
			if streamNode.weight == currentHighWeight {
				sch.renewQuantum()
			}
		}
		strm = streamNode
		utils.Debugf("ytxing: traverse, stream %v has sth to send", streamNode.id)
	} else if flag == 1 {
		for i := 0; i < sch.openStreams; i++ {
			strm = sch.traversePRR(sch.startStreamIdPRR, 0)
			if strm != nil {
				break
			}
		}
	}
	utils.Infof("this stream %v\n", sch.startStreamIdPRR)
	return
}
func (sch *streamScheduler) PRRSchedule() *node {
	sch.Lock()
	defer sch.Unlock()
	utils.Debugf("zy: PRRschedule() IN \n")
	n := sch.traversePRR(sch.startStreamIdPRR, 1)
	if n == nil {
		utils.Debugf("zy: PRRschedule() OUT, return stream nil")
	} else {
		utils.Debugf("zy: PRRschedule() OUT, return stream %v", n.id)
	}
	return n
}
