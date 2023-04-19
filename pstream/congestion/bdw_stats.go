package congestion

import (
	"time"

	"github.com/lucas-clemente/pstream/internal/protocol"
	"github.com/lucas-clemente/pstream/internal/utils"
)

const (
	rttRound uint8 = 3
)

// BDWStats provides estimated bandwidth statistics
type BDWStats struct {
	bandwidth       Bandwidth //  bit per second
	compareWindow   [10]Bandwidth
	roundRobinIndex uint8 //  resume where ended
	// bytesReceived   protocol.ByteCount //ytxing
	// lastUpdateTime  time.Time          //ytxing
	RTTStats *RTTStats
}

// NewBDWStats makes a properly initialized BDWStats object
func NewBDWStats(bandwidth Bandwidth) *BDWStats {
	return &BDWStats{
		bandwidth: bandwidth,
	}
}

//GetBandwidth returns estimated bandwidth in bps
func (b *BDWStats) GetBandwidth() Bandwidth { return b.bandwidth }

// UpdateBDW updates the bandwidth based on a new sample.
func (b *BDWStats) UpdateBDW(sentDelta protocol.ByteCount, sentDelay time.Duration) {
	disable := false
	if !disable {
		bdw := Bandwidth(sentDelta) * Bandwidth(time.Second) / Bandwidth(sentDelay) * BytesPerSecond
		b.bandwidth = bdw
		size := uint8(len(b.compareWindow))
		startIndex := b.roundRobinIndex
		b.compareWindow[(startIndex)%size] = bdw

		b.roundRobinIndex = (b.roundRobinIndex + 1) % size

		for i := uint8(0); i < size; i++ {
			utils.Debugf("update when b.bandwidth %v < b.compareWindow[%v] %v", b.bandwidth, i, b.compareWindow[i])
			if b.bandwidth < b.compareWindow[i] {

				b.bandwidth = b.compareWindow[i]
			}
		}

	}
}

// func (b *BDWStats) UpdateBDWCwnd(sentDelta protocol.ByteCount, sentDelay time.Duration) {
// 	if sentDelay == 0 {
// 		return
// 	}
// 	b.bandwidth = Bandwidth(sentDelta) * Bandwidth(time.Second) / Bandwidth(sentDelay) * BytesPerSecond
// }
// func (b *BDWStats) UpdateBytes(bytes protocol.ByteCount) {
// 	b.bytesReceived += bytes
// 	rtt := b.RTTStats.smoothedRTT
// 	if time.Now().After(b.lastUpdateTime.Add(time.Duration(uint8(rtt) * rttRound))) {
// 		utils.Debugf("ytxing: UpdateBytes %v after %v", b.bandwidth/1e6, time.Since(b.lastUpdateTime))
// 		b.bandwidth = Bandwidth(b.bytesReceived * protocol.ByteCount(BytesPerSecond) * protocol.ByteCount(time.Second) / protocol.ByteCount(time.Since(b.lastUpdateTime)))
// 		b.bytesReceived = 0
// 		b.lastUpdateTime = time.Now()
// 	}
// }
