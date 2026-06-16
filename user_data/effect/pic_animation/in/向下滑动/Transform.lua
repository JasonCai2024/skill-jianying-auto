local exports = exports or {}
local Transform = Transform or {}
Transform.__index = Transform

local function getBezierValue(controls, t)
    local ret = {}
    local xc1 = controls[1]
    local yc1 = controls[2]
    local xc2 = controls[3]
    local yc2 = controls[4]
    ret[1] = 3*xc1*(1-t)*(1-t)*t+3*xc2*(1-t)*t*t+t*t*t
    ret[2] = 3*yc1*(1-t)*(1-t)*t+3*yc2*(1-t)*t*t+t*t*t
    return ret
end

local function getBezierDerivative(controls, t)
    local ret = {}
    local xc1 = controls[1]
    local yc1 = controls[2]
    local xc2 = controls[3]
    local yc2 = controls[4]
    ret[1] = 3*xc1*(1-t)*(1-3*t)+3*xc2*(2-3*t)*t+3*t*t
    ret[2] = 3*yc1*(1-t)*(1-3*t)+3*yc2*(2-3*t)*t+3*t*t
    return ret
end

local function getBezierTfromX(controls, x)
    local ts = 0
    local te = 1
    -- divide and conque
    repeat
        local tm = (ts+te)/2
        local value = getBezierValue(controls, tm)
        if(value[1]>x) then
            te = tm
        else
            ts = tm
        end
    until(te-ts < 0.0001)

    return (te+ts)/2
end

-- ================自定义曲线================

local function funcEaseAction1(t, b, c, d)
    t = t/d
    -- 第一阶段的位移曲线，贝塞尔曲线版本
    local controls = {0.39, 0.575, 0.565, 1}
    local tvalue = getBezierTfromX(controls, t)
    local value =  getBezierValue(controls, tvalue)
    return b + c * value[2]
end

local function funcEaseAction2(t, b, c, d)
    t = t/d
    -- 第一阶段的位移曲线，贝塞尔曲线版本
    local controls = {0, 0, 1, 1}
    local tvalue = getBezierTfromX(controls, t)
    local value =  getBezierValue(controls, tvalue)
    return b + c * value[2]
end

local function funcEaseAction3(t, b, c, d)
    t = t/d
    -- 第一阶段的位移曲线，贝塞尔曲线版本
    local controls = {0, 0, 1, 1}
    local tvalue = getBezierTfromX(controls, t)
    local value =  getBezierValue(controls, tvalue)
    return b + c * value[2]
end

local function funcEaseAction4(t, b, c, d)
    t = t/d
    -- 第一阶段的位移曲线，贝塞尔曲线版本
    local controls = {0, 0, 1, 1}
    local tvalue = getBezierTfromX(controls, t)
    local value =  getBezierValue(controls, tvalue)
    return b + c * value[2]
end

-- ================自定义曲线================

function Transform.new(construct, ...)
    local self = setmetatable({}, Transform)
    self.material = nil
    self.duration = 0
    self.values = {}
    
    -- 配置动画效果
    self.actions = 
    {
        -- 位移
        {
            startPosition = Amaz.Vector3f(0.0, -1.0, 0.0),
            endPosition = Amaz.Vector3f(0.0, 0.0, 0.0),
            actionFunction = funcEaseAction1,
            startTime = 0.0,
            endTime = 1.0
        },
        -- 缩放
        {
            startScale = Amaz.Vector3f(1.0, 1.0, 1.0),
            endScale = Amaz.Vector3f(1.0, 1.0, 1.0),
            actionFunction = funcEaseAction2,
            startTime = 0.0,
            endTime = 1.0
        },
        -- 旋转
        {
            startRotate = Amaz.Vector3f(0.0, 0.0, 0.0),
            endRotate = Amaz.Vector3f(0.0, 0.0, 0.0),
            actionFunction = funcEaseAction3,
            startTime = 0.0,
            endTime = 1.0
        },
        -- 不透明度
        {
            startAlpha = 0.0,
            endAlpha = 1.0,
            actionFunction = funcEaseAction4,
            startTime = 0.0,
            endTime = 0.2
        },
        {
            -- 模糊强度 --设置为0表示关闭镜像
            blurIntensity = 0.0,
            -- 模糊类型，0不模糊，1方向，2缩放
            blurType = 0,
            -- 模糊方向，不可以写成0，0
            blurDirection = Amaz.Vector2f(1, 0),
            -- 动画曲线
            actionFunction = Amaz.Ease.linear,
            -- 起始时间
            startTime = 0.0,
            -- 结束时间
            endTime = 1.0
        },
    }

    if construct and Transform.constructor then Transform.constructor(self, ...) end
    return self
end

function Transform:constructor()

end

function Transform:onStart(comp)
    self.vfx = comp.entity.scene:findEntityBy("Blur")
    self.canvas = comp.entity.scene:findEntityBy("Root")
    self.blend = comp.entity.scene:findEntityBy("Canvas")
    local transform = comp.entity:getComponent("Transform")
    transform.localPosition = Amaz.Vector3f(0.0, 0.0, 0.0)
    self.material = self.vfx:getComponent("Sprite2DRenderer").material
    if self.blend ~= nil then
        self.blendMaterial = self.blend:getComponent("Sprite2DRenderer").material
    end
    self.tweenDirty = true
end

-- 编辑器测试用方法，更新资源包前要注释掉！！！
-- function Transform:onUpdate(comp, deltaTime)
--     if self.tweenDirty then
--         self.blend = comp.entity.scene:findEntityBy("Root")
--         self.blendMaterial = self.blend:getComponent("Sprite2DRenderer").material

--         self.time = 0.0
--         -- 测试代码，修改动画时间
--         self.duration = 3.0
--         -- 设置多少秒后重复
--         self.resetDuration = 3.5

--         for i = 1, #self.actions do
--             local action = self.actions[i]
--             if action.startPosition ~= nil then
--                 action.startPosition.y = -action.startPosition.y
--             end
--             if action.endPosition ~= nil then
--                 action.endPosition.y = -action.endPosition.y
--             end
--             if action.startRotate ~= nil then
--                 action.startRotate.z = -action.startRotate.z
--             end
--             if action.endRotate ~= nil then
--                 action.endRotate.z = -action.endRotate.z
--             end

--         end

--     end

--     self.time = self.time + deltaTime

--     if self.time > self.duration then
--         self:seek(self.duration)
--     else
--         self:seek(self.time)
--     end
    
--     if self.time > self.resetDuration then
--         self.time = 0.0
--     end
-- end

local function checkDirty(self)
    if self.tweenDirty then
        local transform = self.vfx:getComponent("Transform")
        local screenW = Amaz.BuiltinObject:getOutputTextureWidth()
        local screenH = Amaz.BuiltinObject:getOutputTextureHeight()
        local ratio = screenW / screenH

        for i = 1, #self.actions do
            local action = self.actions[i]
            local from = {}
            local to = {}
            local target = nil;
            if action.startPosition ~= nil then
                target = transform
                action.startPosition.x = action.startPosition.x * ratio
                from["localPosition"] = action.startPosition
            end

            if action.startScale ~= nil then
                target = transform
                from["localScale"] = action.startScale
            end

            if action.startRotate ~= nil then
                target = transform
                from["localEulerAngle"] = action.startRotate
            end


            if action.endPosition ~= nil then
                target = transform
                action.endPosition.x = action.endPosition.x * ratio
                to["localPosition"] = action.endPosition
            end

            if action.endScale ~= nil then
                target = transform
                to["localScale"] = action.endScale
            end

            if action.endRotate ~= nil then
                target = transform
                to["localEulerAngle"] = action.endRotate
            end

            if action.endRotate ~= nil then
                target = transform
                to["localEulerAngle"] = action.endRotate
            end
            
            if action.blurType ~= nil then
                target = self.material
                self.material:enableMacro("BLUR_TYPE", 1)
                self.material["blurDirection"] = action.blurDirection
                from["blurStep"] = action.blurIntensity / (self.duration * (action.endTime - action.startTime))
                to["blurStep"] = 0.0
            end

            if action.startAlpha ~= nil then
                target = self.blendMaterial
                from["_alpha"] = action.startAlpha
            end

            if action.endAlpha ~= nil then
                target = self.blendMaterial
                to["_alpha"] = action.endAlpha
            end

            if action.key ~= nil then
                target = self.values
                from[action.key] = action.startValue
                to[action.key] = action.endValue
            end

            action.tween = self.canvas.scene.tween:fromTo(target, 
                                                             from,
                                                             to,
                                                             self.duration * (action.endTime - action.startTime),
                                                             action.actionFunction,
                                                             nil, 
                                                             0.0, 
                                                             nil, 
                                                             false)            

        end
                                                
        self.tweenDirty = false

    end
end


local function updateHandle(entity, canvas)
    if entity == nil then
        return
    end

    local animTrans = entity:getComponent("Transform")
    local parentTrans = canvas:getComponent("Transform")
    -- 拆分用户操作的TRS
    local userS = parentTrans.localScale
    local userR = parentTrans.localOrientation
    local userT = parentTrans.localPosition

    -- 拆分动画操作的TRS
    local animS = animTrans.localScale
    local animR = animTrans.localOrientation
    local animT = animTrans.localPosition

    local mat = parentTrans.localMatrix

    local matA = animTrans.localMatrix

    -- userM为用户操作的缩放和旋转
    local userM = parentTrans.localMatrix
    userM:SetTRS(Amaz.Vector3f(0.0, 0.0, 0.0), userR, userS)

    -- move to (0,0)
    -- matA为动画的Transform+用户的位移
    matA:SetTRS(animT, animR, animS)
    matA:AddTranslate(userT)

    -- 因为动画的Entity是用户的Entity的子节点
    -- 所以重新组合transform之前，先右乘父节点的逆矩阵
    animTrans.localMatrix = matA * userM * parentTrans.localMatrix:Invert_Full()
end

function Transform:seek(time)
    checkDirty(self)
    -- 将视频的Transform设置为单位矩阵，不然会残留上一次seek的值
    local animTrans = self.vfx:getComponent("Transform")
    animTrans.localMatrix = animTrans.localMatrix:SetIdentity()
    self.blendMaterial["_alpha"] = 1.0

    -- seek之前先将自定义属性的值设置成默认值，不然会残留上一次seek的值
    for i = 1, #self.actions do
        local action = self.actions[i]
        if action.key ~= nil then
            action.actionHandle(self, action.key, action.defaultValue)
        end
    end

    -- 根据每一个动画的时间和属性seek
    for i = 1, #self.actions do
        local action = self.actions[i]
        local normalTime = time / self.duration

        if normalTime >= action.startTime and normalTime <= action.endTime then
            if action.blurType ~= nil then
                self.material:enableMacro("BLUR_TYPE", action.blurType)
            end
            action.tween:set(time - action.startTime * self.duration)
            if action.key ~= nil then
                action.actionHandle(self, action.key, self.values[action.key])
            end
        end
    end
    
    -- 调整用户操作视频的TRS和动画TRS的先后顺序
    -- 用户的缩放和旋转在第一和第二阶段
    -- 用户的拖动是在最后一个阶段
    -- 否则会和动画效果有冲突
    updateHandle(self.vfx, self.canvas)
end

function Transform:setDuration(duration)
    self.duration = duration
    self.tweenDirty = true
end

function Transform:clear()
    self.tweenDirty = true
    -- 将视频的Transform设置为单位矩阵，不然会残留上一次seek的值
    local animTrans = self.vfx:getComponent("Transform")
    animTrans.localMatrix = animTrans.localMatrix:SetIdentity()
    self.blendMaterial["_alpha"] = 1.0

    -- seek之前先将自定义属性的值设置成默认值，不然会残留上一次seek的值
    for i = 1, #self.actions do
        local action = self.actions[i]
        if action.key ~= nil and action.defaultValue ~= nil then
            action.actionHandle(self, action.key, action.defaultValue)
        end
    end
end
exports.Transform = Transform
return exports
