namespace CHSH {

    import Std.Math.*;
    import Std.Arrays.*;

    operation PrepareBellPair(a : Qubit, b : Qubit) : Unit {
        H(a);
        CNOT(a, b);
    }

    // kontrol icin: entangle olmayan |+>|+>
    operation PrepareProductPair(a : Qubit, b : Qubit) : Unit {
        H(a);
        H(b);
    }

    // Q# sadece Z'de olcuyor, Ry(-theta) ile istenen ekseni Z'ye ceviriyorum
    operation MeasureAtAngle(theta : Double, q : Qubit) : Result {
        Ry(-theta, q);
        return MResetZ(q);
    }

    operation SampleCorrelation(
        angleA : Double,
        angleB : Double,
        entangled : Bool
    ) : Int {
        use (a, b) = (Qubit(), Qubit());
        if entangled {
            PrepareBellPair(a, b);
        } else {
            PrepareProductPair(a, b);
        }
        let ra = MeasureAtAngle(angleA, a);
        let rb = MeasureAtAngle(angleB, b);
        let sa = ra == Zero ? 1 | -1;
        let sb = rb == Zero ? 1 | -1;
        return sa * sb;
    }

    operation SampleCorrelationBatch(
        angleA : Double,
        angleB : Double,
        entangled : Bool,
        shots : Int
    ) : Int[] {
        mutable products = [0, size = shots];
        for i in 0..shots - 1 {
            set products w/= i <- SampleCorrelation(angleA, angleB, entangled);
        }
        return products;
    }
}
