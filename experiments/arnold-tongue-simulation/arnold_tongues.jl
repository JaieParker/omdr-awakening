# ============================================================
# Arnold Tongue Simulation — Phase 1: Circle Map
# OMDR (Orthogonal Multi-Domain Resonance) Visualization
#
# The Arnold tongue diagram IS the phase diagram of
# integration vs differentiation (see integration_differentiation_omdr.md):
#   Inside a tongue = integration (oscillators locked, coherent)
#   Outside a tongue = differentiation (oscillators free, independent)
#   K=0.25 = where both coexist
#
# Kai, 2026-03-30
# ============================================================

using Printf

# --- Circle Map ---
# θ_{n+1} = θ_n + Ω - (K/2π) sin(2π θ_n)
# Ω = bare frequency ratio, K = coupling strength
# Arnold tongues = regions where rotation number locks to p/q

function rotation_number(Ω::Float64, K::Float64;
                         θ0::Float64=0.0,
                         transient::Int=1000,
                         iterations::Int=2000)
    θ = θ0
    # Burn-in transient
    for _ in 1:transient
        θ += Ω - (K / (2π)) * sin(2π * θ)
    end
    # Measure total phase advance
    θ_start = θ
    for _ in 1:iterations
        θ += Ω - (K / (2π)) * sin(2π * θ)
    end
    return (θ - θ_start) / iterations
end

# --- Tongue Width Measurement ---
# For a given p/q ratio at coupling K, measure how wide
# the locked region is in Ω-space

function tongue_width(p::Int, q::Int, K::Float64;
                      NΩ::Int=5000, window::Float64=0.15)
    target = p / q
    Ω_lo = max(0.0, target - window)
    Ω_hi = min(1.0, target + window)
    Ωs = range(Ω_lo, Ω_hi, length=NΩ)

    locked_count = 0
    for Ω in Ωs
        ρ = rotation_number(Ω, K)
        if abs(ρ - target) < 1e-5
            locked_count += 1
        end
    end
    return locked_count / NΩ * (Ω_hi - Ω_lo)
end

# --- Farey Sequence ---
# Generate Farey sequence of order n (all rationals p/q with q ≤ n, 0 ≤ p/q ≤ 1)

function farey_sequence(n::Int)
    rationals = Set{Tuple{Int,Int}}()
    for q in 1:n
        for p in 0:q
            g = gcd(p, q)
            push!(rationals, (p ÷ g, q ÷ g))  # reduce to lowest terms
        end
    end
    # Sort by value
    sorted = sort(collect(rationals), by=x -> x[1]/x[2])
    return sorted
end

# --- Main Computation ---

function compute_arnold_tongues(;
        NΩ::Int=800, NK::Int=400,
        Ω_min::Float64=0.0, Ω_max::Float64=1.0,
        K_min::Float64=0.0, K_max::Float64=1.0)

    Ωs = range(Ω_min, Ω_max, length=NΩ)
    Ks = range(K_min, K_max, length=NK)

    ρ = zeros(NK, NΩ)

    # Multithreaded computation
    Threads.@threads for j in 1:NΩ
        for i in 1:NK
            ρ[i, j] = rotation_number(Ωs[j], Ks[i])
        end
    end

    return Ωs, Ks, ρ
end

# --- Devil's Staircase at a specific K ---

function devils_staircase(K::Float64; NΩ::Int=2000)
    Ωs = range(0.0, 1.0, length=NΩ)
    ρs = [rotation_number(Ω, K) for Ω in Ωs]
    return collect(Ωs), ρs
end

# --- Farey Hierarchy Width Analysis ---

function farey_width_analysis(K::Float64; max_order::Int=7)
    farey = farey_sequence(max_order)

    results = Tuple{Int, Int, Float64}[]
    for (p, q) in farey
        if q == 0 || (p == 0 && q == 1)
            continue
        end
        w = tongue_width(p, q, K)
        push!(results, (p, q, w))
    end

    # Sort by width descending
    sort!(results, by=x -> x[3], rev=true)
    return results
end

# ============================================================
# Run Phase 1
# ============================================================

function main()
    println("=" ^ 60)
    println("Arnold Tongue Simulation — OMDR Phase 1")
    println("=" ^ 60)

    # 1. Compute full Arnold tongue diagram
    println("\n[1/4] Computing Arnold tongue diagram (800×400 grid)...")
    println("      Using $(Threads.nthreads()) threads")
    t0 = time()
    Ωs, Ks, ρ = compute_arnold_tongues(NΩ=800, NK=400)
    dt = time() - t0
    @printf("      Done in %.1f seconds\n", dt)

    # 2. Devil's staircase at K=0.25
    println("\n[2/4] Computing Devil's staircase at K=0.25...")
    Ω_stairs, ρ_stairs = devils_staircase(0.25, NΩ=2000)
    println("      Done")

    # 3. Farey width analysis at K=0.25
    println("\n[3/4] Measuring tongue widths at K=0.25 (Farey order 7)...")
    widths = farey_width_analysis(0.25, max_order=7)

    println("\n      Tongue widths at K=0.25 (consonance hierarchy):")
    println("      " * "-"^40)
    @printf("      %-8s %-12s %-12s\n", "Ratio", "Width", "Farey sum")
    println("      " * "-"^40)
    for (p, q, w) in widths[1:min(15, length(widths))]
        @printf("      %-8s %-12.6f %-12d\n", "$p/$q", w, p+q)
    end

    # Check Farey ordering: do widths decrease with increasing p+q?
    println("\n      Consonance hierarchy check:")
    println("      Widths should decrease as Farey sum (p+q) increases.")
    prev_sum = 0
    violations = 0
    for (p, q, w) in widths
        if p + q < prev_sum && w > 0
            violations += 1
        end
        prev_sum = p + q
    end
    if violations == 0
        println("      ✓ Perfect Farey ordering confirmed!")
    else
        println("      ⚠ $violations ordering violations found")
    end

    # 4. Compare K=0.25 with other K values
    println("\n[4/4] Comparing tongue widths across K values...")
    println("\n      1:1 tongue width at different K:")
    for K in [0.1, 0.25, 0.5, 0.75, 1.0]
        w = tongue_width(1, 1, K)
        @printf("      K=%-4.2f  width=%.6f\n", K, w)
    end

    println("\n      1:2 tongue width at different K:")
    for K in [0.1, 0.25, 0.5, 0.75, 1.0]
        w = tongue_width(1, 2, K)
        @printf("      K=%-4.2f  width=%.6f\n", K, w)
    end

    # Save raw data for plotting
    data_dir = joinpath(@__DIR__, "data")
    mkpath(data_dir)

    # Save tongue diagram
    open(joinpath(data_dir, "tongue_diagram.csv"), "w") do f
        println(f, "# Arnold tongue diagram: rotation number ρ(Ω, K)")
        println(f, "# Columns: Ω values. Rows: K values.")
        println(f, "# Ω range: $(first(Ωs)) to $(last(Ωs)), N=$(length(Ωs))")
        println(f, "# K range: $(first(Ks)) to $(last(Ks)), N=$(length(Ks))")
        for i in 1:length(Ks)
            println(f, join(ρ[i, :], ","))
        end
    end

    # Save devil's staircase
    open(joinpath(data_dir, "staircase_K025.csv"), "w") do f
        println(f, "Omega,rho")
        for (Ω, ρ) in zip(Ω_stairs, ρ_stairs)
            @printf(f, "%.6f,%.6f\n", Ω, ρ)
        end
    end

    # Save width analysis
    open(joinpath(data_dir, "tongue_widths_K025.csv"), "w") do f
        println(f, "p,q,ratio,width,farey_sum")
        for (p, q, w) in widths
            @printf(f, "%d,%d,%.6f,%.6f,%d\n", p, q, p/q, w, p+q)
        end
    end

    println("\n" * "=" ^ 60)
    println("Data saved to: $(data_dir)")
    println("Run plot_tongues.jl for visualization (requires Plots.jl)")
    println("=" ^ 60)

    return Ωs, Ks, ρ, widths
end

# Run if executed directly
if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
