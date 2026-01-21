#pragma once

#include "od_integer.h"

namespace OD
{
    template<typename T>
    struct Value
    {
        using DataType = T;
        constexpr Value() = default;
        constexpr Value(const Value&) = default;
        constexpr Value(Value&&) = default;
        constexpr Value& operator=(const Value&) = default;
        constexpr Value& operator=(Value&&) = default;
        constexpr Value(const DataType& value) : m_Value(value) {}
        constexpr Value(DataType&& value) : m_Value(std::move(value)) {}
        constexpr Value& operator=(const DataType& value)
        {
            m_Value = value;
            return *this;
        }
        constexpr Value& operator=(DataType&& value)
        {
            m_Value = std::move(value);
            return *this;
        }
        constexpr operator const DataType&() const noexcept
        {
            return m_Value;
        }
        constexpr operator DataType&() noexcept
        {
            return m_Value;
        }
        constexpr const DataType& getValue() const noexcept
        {
            return m_Value;
        }
        constexpr void setValue(const DataType& value) noexcept
        {
            m_Value = value;
        }
        constexpr DataType& operator->() noexcept
        {
            return m_Value;
        }
        constexpr const DataType& operator->() const noexcept
        {
            return m_Value;
        }        
        constexpr auto operator<=>(const Value& other) const noexcept = default;
    private:
        DataType m_Value{};
    };

    template <>
    struct Value<void>
    {
    };
}