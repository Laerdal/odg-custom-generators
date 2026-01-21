#pragma once

#include <compare>
#include <cstdint>
#include <sstream>
#include <string>
#include <vector>

namespace OD
{
    template<uint8_t BITS, bool SIGNED> class Integer
    {
    public:
        static_assert(BITS == 40 || BITS == 48 || BITS == 56, "Only support bit sizes of 40, 48, or 56");
        static constexpr uint8_t ByteSize {BITS / 8};
        using ValueType = typename std::conditional_t < SIGNED, std::conditional_t < ByteSize<4, int32_t, int64_t>,
              std::conditional_t<ByteSize<4, uint32_t, uint64_t>>;

        constexpr Integer() = default;

        constexpr Integer(ValueType value):
            m_Value(value)
        {
        }

        constexpr ValueType get() const
        {
            return m_Value;
        }

        constexpr void set(ValueType value)
        {
            m_Value = value;
        }

        constexpr ValueType& data()
        {
            return m_Value;
        }

        const constexpr ValueType& data() const
        {
            return m_Value;
        }

        constexpr auto operator<=>(const Integer<BITS, SIGNED>& other) const = default;

        std::string toString() const
        {
            std::ostringstream oss;
            oss << std::hex << std::showbase << m_Value;
            return oss.str();
        }

    private:
        ValueType m_Value {};
    };

    using Boolean = bool;
    using Int8 = int8_t;
    using Int16 = int16_t;
    using Int24 = Integer<24, true>;
    using Int32 = int32_t;
    using Int40 = Integer<40, true>;
    using Int48 = Integer<48, true>;
    using Int56 = Integer<56, true>;
    using Int64 = int64_t;
    using UInt8 = uint8_t;
    using UInt16 = uint16_t;
    using UInt24 = Integer<24, false>;
    using UInt32 = uint32_t;
    using UInt40 = Integer<40, false>;
    using UInt48 = Integer<48, false>;
    using UInt56 = Integer<56, false>;
    using UInt64 = uint64_t;
    using Real32 = float;
    using Real64 = double;
    using VisibleString = std::string;
    using OctetString = std::vector<std::byte>;
    using Unknown = void;
} // namespace OD
